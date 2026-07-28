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

async function collectListings(page) {
  return page.$$eval('a[href*="/marketplace/item/"]', (links) =>
    links.map((a) => ({
      href: a.href.split("?")[0],
      text: a.innerText || "",
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
    await notify({
      title: `${search.name}: ${price}`,
      body: title,
      url: item.href,
    });
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
