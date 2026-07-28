// PriceLens comps server — runs on your PC.
//
// Serves the PriceLens app AND a /comps endpoint that pulls real eBay
// sold-listings results through a local browser, the same way you would by
// hand. No eBay login, no account involved. Results are cached for a day
// and requests are spaced out so the usage looks like a person browsing.
//
//   npm install
//   node server.js
//   → open http://localhost:8484 (or http://<your-pc-ip>:8484 from your phone)

import { chromium } from "playwright";
import http from "http";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const ROOT = dirname(fileURLToPath(import.meta.url));
const PORT = process.env.PORT || 8484;
const HEADED = process.env.HEADED === "1"; // set HEADED=1 if results come back empty

const cache = new Map(); // query -> { at, data }
const CACHE_MS = 24 * 60 * 60 * 1000;
const MIN_GAP_MS = 5000; // never hit eBay faster than this
let lastFetch = 0;
let queue = Promise.resolve();

let context = null;
async function getContext() {
  if (!context) {
    context = await chromium.launchPersistentContext(join(ROOT, "ebay-profile"), {
      channel: "chrome",
      headless: !HEADED,
      viewport: { width: 1280, height: 900 },
    });
  }
  return context;
}

function stats(prices) {
  const p = [...prices].sort((a, b) => a - b);
  const q = (f) => p[Math.min(p.length - 1, Math.floor(f * p.length))];
  return { low: q(0.1), median: q(0.5), high: q(0.9) };
}

async function fetchComps(query) {
  const url =
    "https://www.ebay.com/sch/i.html?_nkw=" +
    encodeURIComponent(query) +
    "&LH_Sold=1&LH_Complete=1&_ipg=60";

  const ctx = await getContext();
  const page = await ctx.newPage();
  try {
    // pace like a human
    const wait = lastFetch + MIN_GAP_MS - Date.now();
    if (wait > 0) await new Promise((r) => setTimeout(r, wait));
    lastFetch = Date.now();

    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(2500);

    const items = await page.$$eval(".s-item", (nodes) =>
      nodes.map((n) => ({
        title: n.querySelector(".s-item__title")?.innerText ?? "",
        price: n.querySelector(".s-item__price")?.innerText ?? "",
      }))
    );

    const samples = items
      .filter((i) => i.title && !/shop on ebay/i.test(i.title))
      .map((i) => {
        const m = i.price.match(/\$([\d,]+(?:\.\d{2})?)/);
        return m
          ? { title: i.title.slice(0, 90), price: Number(m[1].replace(/,/g, "")) }
          : null;
      })
      .filter(Boolean)
      .filter((i) => i.price > 0);

    if (samples.length === 0) {
      return { query, count: 0, url, note: "No sold results parsed — eBay may have changed markup or blocked this fetch. Try HEADED=1." };
    }

    const s = stats(samples.map((i) => i.price));
    return {
      query,
      count: samples.length,
      low: s.low,
      median: s.median,
      high: s.high,
      samples: samples.slice(0, 8),
      url,
    };
  } finally {
    await page.close();
  }
}

const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css" };

http
  .createServer(async (req, res) => {
    const u = new URL(req.url, `http://${req.headers.host}`);

    if (u.pathname === "/comps") {
      const q = (u.searchParams.get("q") || "").trim();
      if (!q) {
        res.writeHead(400, { "content-type": "application/json" });
        return res.end(JSON.stringify({ error: "missing q" }));
      }
      const hit = cache.get(q.toLowerCase());
      if (hit && Date.now() - hit.at < CACHE_MS) {
        res.writeHead(200, { "content-type": "application/json" });
        return res.end(JSON.stringify({ ...hit.data, cached: true }));
      }
      // serialize eBay fetches through a queue
      queue = queue.then(async () => {
        try {
          const data = await fetchComps(q);
          if (data.count > 0) cache.set(q.toLowerCase(), { at: Date.now(), data });
          res.writeHead(200, { "content-type": "application/json" });
          res.end(JSON.stringify(data));
          console.log(`[comps] "${q}" → ${data.count} results, median $${data.median ?? "?"}`);
        } catch (err) {
          console.error(`[comps] "${q}" failed:`, err.message);
          res.writeHead(500, { "content-type": "application/json" });
          res.end(JSON.stringify({ error: err.message }));
        }
      });
      return;
    }

    // static: serve the app
    const file = u.pathname === "/" ? "/index.html" : u.pathname;
    try {
      const body = readFileSync(join(ROOT, file.replace(/\.\./g, "")));
      res.writeHead(200, { "content-type": MIME[file.slice(file.lastIndexOf("."))] || "application/octet-stream" });
      res.end(body);
    } catch {
      res.writeHead(404);
      res.end("not found");
    }
  })
  .listen(PORT, () => {
    console.log(`PriceLens server running:`);
    console.log(`  on this PC:      http://localhost:${PORT}`);
    console.log(`  from your phone: http://<this-pc's-ip>:${PORT}  (same wifi, or Tailscale)`);
  });
