// FlipWatch — local Facebook Marketplace watcher.
//
// Runs a real, visible Chrome window with a persistent profile you log into
// once. On a timer it visits each search URL from config.json, collects the
// listings on the page, and pushes a phone notification (via ntfy.sh) for
// anything it hasn't seen before. It never sends messages, never buys, and
// never runs headless — it is deliberately a browser that refreshes itself
// at a human pace, nothing more.

import { chromium } from "playwright";
import { readFileSync, writeFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const ROOT = dirname(fileURLToPath(import.meta.url));
const CONFIG_PATH = join(ROOT, "config.json");
const SEEN_PATH = join(ROOT, "seen.json");
const PROFILE_DIR = join(ROOT, "fb-profile");

if (!existsSync(CONFIG_PATH)) {
  console.error(
    "No config.json found. Copy config.example.json to config.json and fill it in."
  );
  process.exit(1);
}

const config = JSON.parse(readFileSync(CONFIG_PATH, "utf8"));
const seen = existsSync(SEEN_PATH)
  ? new Set(JSON.parse(readFileSync(SEEN_PATH, "utf8")))
  : new Set();
let firstRun = !existsSync(SEEN_PATH);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const rand = (min, max) => min + Math.random() * (max - min);

function withinActiveHours() {
  const h = new Date().getHours();
  const { start = 7, end = 23 } = config.activeHours ?? {};
  return start <= end ? h >= start && h < end : h >= start || h < end;
}

function saveSeen() {
  // Cap the file so it doesn't grow forever; old listings are long gone anyway.
  const ids = [...seen];
  writeFileSync(SEEN_PATH, JSON.stringify(ids.slice(-5000)));
}

async function notify({ title, body, url }) {
  const topic = config.ntfyTopic;
  if (!topic) {
    console.log(`[notify skipped — no ntfyTopic] ${title} :: ${body}`);
    return;
  }
  try {
    await fetch(`https://ntfy.sh/${topic}`, {
      method: "POST",
      body,
      headers: {
        Title: title,
        Priority: "high",
        Click: url,
        Tags: "moneybag",
      },
    });
  } catch (err) {
    console.error("ntfy push failed:", err.message);
  }
}

function parseListing(text) {
  // Card text is typically like "$120Solid wood dresserNew Bern, NC".
  const priceMatch = text.match(/\$[\d,]+/);
  const price = priceMatch ? priceMatch[0] : "$?";
  const title = text
    .replace(/\$[\d,]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 90);
  return { price, title };
}

function priceNumber(price) {
  const n = Number(price.replace(/[^0-9]/g, ""));
  return Number.isFinite(n) && n > 0 ? n : null;
}

// ----- Profit pipeline: title → eBay search query → real comps → fee math -----

async function identifyListing(title, askPrice, imageUrl) {
  const prompt = `You triage Facebook Marketplace listings for a reseller in New Bern, NC. Given a listing title, asking price${imageUrl ? ", and the listing photo" : ""}, decide whether it's a specific, identifiable item worth checking eBay sold comps for.${imageUrl ? " Use the photo to pin down brand/model when the title is vague." : ""}

Listing title: "${title}"
Asking price: $${askPrice ?? "unknown"}

Reply with ONLY a JSON object, no code fence:
{"skip":false,"reason":"short","item":"what it actually is","search_query":"the exact eBay sold-listings search a reseller would run (brand + model, no filler)","platform":"eBay|Mercari|Facebook local","ship_cost":0}

skip:true only when even the photo doesn't reveal a specific resellable item, or it's a service, rental, or obvious junk. platform: "Facebook local" for heavy/bulky items (ship_cost 0). ship_cost: estimated USD to ship if sold online.`;

  const content = imageUrl
    ? [{ type: "image", source: { type: "url", url: imageUrl } }, { type: "text", text: prompt }]
    : prompt;

  const call = async (body) => {
    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": config.anthropicApiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`anthropic HTTP ${res.status}`);
    return res.json();
  };

  let msg;
  const base = { model: config.model || "claude-opus-5", max_tokens: 1000 };
  try {
    msg = await call({ ...base, messages: [{ role: "user", content }] });
  } catch (err) {
    // Facebook CDN image URLs expire; if the image fetch broke the request,
    // retry on the title alone rather than losing the listing.
    if (imageUrl) msg = await call({ ...base, messages: [{ role: "user", content: prompt }] });
    else throw err;
  }
  if (msg.stop_reason === "refusal") return { skip: true, reason: "refused" };
  const text = msg.content.filter((b) => b.type === "text").map((b) => b.text).join("\n");
  const start = text.lastIndexOf("{");
  return JSON.parse(text.slice(start, text.lastIndexOf("}") + 1));
}

async function getComps(query) {
  const base = (config.compsUrl || "http://localhost:8484").replace(/\/$/, "");
  const res = await fetch(`${base}/comps?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error(`comps HTTP ${res.status}`);
  return res.json();
}

function feeMath(platform, price, shipCost) {
  let fees = 0, ship = shipCost || 0;
  if (/ebay/i.test(platform)) fees = 0.136 * (price + ship) + 0.4;
  else if (/mercari/i.test(platform)) fees = 0.1 * price;
  else { fees = 0; ship = 0; } // Facebook local
  return price - fees - ship;
}

// Returns {notification, deal} if profitable, null if not worth pinging.
async function profitCheck(search, item, title, askPrice) {
  const ident = await identifyListing(title, askPrice, item.img);
  if (ident.skip) {
    console.log(`  skip (${ident.reason}): ${title}`);
    return null;
  }
  const comps = await getComps(ident.search_query);
  if (!comps.count || comps.count < 3) {
    console.log(`  skip (only ${comps.count ?? 0} comps for "${ident.search_query}"): ${title}`);
    return null;
  }
  const net = feeMath(ident.platform, comps.median, ident.ship_cost);
  const profit = askPrice != null ? net - askPrice : null;
  const minProfit = config.minProfit ?? 25;
  if (profit == null || profit < minProfit) {
    console.log(`  skip (est profit $${profit?.toFixed(0) ?? "?"} < $${minProfit}): ${title}`);
    return null;
  }
  return {
    notification: {
      title: `+$${profit.toFixed(0)} est: ${ident.item || title.slice(0, 60)}`,
      body: `Ask $${askPrice} · sells ~$${comps.median.toFixed(0)} (${comps.count} eBay solds) · net ~$${net.toFixed(0)} on ${ident.platform} [${search.name}]`,
      url: item.href,
    },
    deal: {
      item: ident.item || title,
      listingTitle: title,
      ask: askPrice,
      median: comps.median,
      low: comps.low,
      high: comps.high,
      compsCount: comps.count,
      net: Math.round(net),
      profit: Math.round(profit),
      platform: ident.platform,
      query: ident.search_query,
      search: search.name,
      url: item.href,
    },
  };
}

async function postDeal(deal) {
  try {
    const base = (config.compsUrl || "http://localhost:8484").replace(/\/$/, "");
    await fetch(`${base}/deals`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(deal),
    });
  } catch (err) {
    console.error("  deal feed post failed:", err.message);
  }
}

async function collectListings(page) {
  return page.$$eval('a[href*="/marketplace/item/"]', (links) =>
    links.map((a) => ({
      href: a.href.split("?")[0],
      text: a.innerText || "",
      img: a.querySelector("img")?.src || null,
    }))
  );
}

async function checkSearch(page, search) {
  await page.goto(search.url, { waitUntil: "domcontentloaded", timeout: 60000 });
  await sleep(rand(4000, 8000));

  // A gentle scroll loads a screenful more results and looks like reading.
  await page.mouse.wheel(0, rand(600, 1400));
  await sleep(rand(2000, 4000));

  if (page.url().includes("login")) {
    console.log("Facebook wants a login — log in using the open browser window.");
    await notify({
      title: "FlipWatch needs you to log in",
      body: "Facebook logged the watcher browser out. Open the FlipWatch Chrome window and sign in again.",
      url: "https://www.facebook.com/marketplace",
    });
    return { newCount: 0, loggedOut: true };
  }

  const listings = await collectListings(page);
  let newCount = 0;

  for (const item of listings) {
    const idMatch = item.href.match(/\/marketplace\/item\/(\d+)/);
    if (!idMatch) continue;
    const id = idMatch[1];
    if (seen.has(id)) continue;
    seen.add(id);
    newCount++;

    if (firstRun) continue; // seed silently on the first pass — no alert flood

    const { price, title } = parseListing(item.text);
    const n = priceNumber(price);
    if (search.maxPrice && n && n > search.maxPrice) continue;
    if (
      (config.keywordBlocklist ?? []).some((w) =>
        title.toLowerCase().includes(w.toLowerCase())
      )
    )
      continue;

    console.log(`NEW [${search.name}] ${price} — ${title}`);

    if (config.anthropicApiKey) {
      // Smart mode: appraise against real eBay comps; ping only if profitable.
      try {
        const result = await profitCheck(search, item, title, n);
        if (result) {
          await notify(result.notification);
          await postDeal(result.deal);
        }
      } catch (err) {
        // Fail open: if the appraisal pipeline is down, ping the raw listing
        // rather than silently dropping a possible deal.
        console.error(`  appraisal failed (${err.message}) — pinging raw listing`);
        await notify({ title: `${search.name}: ${price}`, body: title, url: item.href });
      }
    } else {
      // No API key configured: original behavior, ping every new listing.
      await notify({ title: `${search.name}: ${price}`, body: title, url: item.href });
    }
    await sleep(rand(500, 1500));
  }

  return { newCount, loggedOut: false };
}

async function main() {
  console.log("FlipWatch starting. A Chrome window will open — leave it running.");
  console.log(
    firstRun
      ? "First run: seeding current listings silently (no notifications yet)."
      : `Loaded ${seen.size} previously seen listings.`
  );

  const context = await chromium.launchPersistentContext(PROFILE_DIR, {
    channel: "chrome",
    headless: false,
    viewport: null,
    args: ["--disable-blink-features=AutomationControlled"],
  });
  const page = context.pages()[0] ?? (await context.newPage());

  // First ever launch: give the user a chance to log in before polling starts.
  await page.goto("https://www.facebook.com/marketplace", {
    waitUntil: "domcontentloaded",
  });
  if (page.url().includes("login")) {
    console.log(
      "Log into Facebook in the open window. Polling starts once you're in (checking every 15s)..."
    );
    while (page.url().includes("login")) await sleep(15000);
    console.log("Logged in. Watching.");
  }

  for (;;) {
    if (!withinActiveHours()) {
      console.log("Outside active hours — sleeping 10 minutes.");
      await sleep(10 * 60 * 1000);
      continue;
    }

    // Randomize order so the pattern isn't identical every cycle.
    const searches = [...config.searches].sort(() => Math.random() - 0.5);
    for (const search of searches) {
      try {
        const { newCount } = await checkSearch(page, search);
        console.log(
          `[${new Date().toLocaleTimeString()}] ${search.name}: ${newCount} new`
        );
      } catch (err) {
        console.error(`[${search.name}] check failed: ${err.message}`);
      }
      saveSeen();
      await sleep(rand(10000, 30000)); // pause between searches, like a person browsing
    }

    if (firstRun) {
      firstRun = false;
      console.log(
        `Seeded ${seen.size} current listings. Notifications begin next cycle.`
      );
    }

    const base = (config.intervalMinutes ?? 5) * 60 * 1000;
    const jitter = rand(0, (config.jitterMinutes ?? 3) * 60 * 1000);
    const next = new Date(Date.now() + base + jitter);
    console.log(`Next sweep ~${next.toLocaleTimeString()}`);
    await sleep(base + jitter);
  }
}

main().catch((err) => {
  console.error("FlipWatch crashed:", err);
  process.exit(1);
});
