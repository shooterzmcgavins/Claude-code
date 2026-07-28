# Morning Setup — The Flip Machine

Everything is in this repo, branch `claude/compounded-interest-game-118ffv`.
Work through this top to bottom; ~45 minutes total, one-time. Tomorrow-you
starts here. ☕

## What you're setting up

| Piece | What it does | Runs |
|---|---|---|
| **PriceLens server** (`pricelens/`) | Your private website: camera appraiser + deals feed. Pulls real eBay sold comps through a local browser. | PC, always on |
| **FlipWatch** (`flipwatch/`) | Watches Facebook Marketplace, appraises every new listing (photo + title → eBay comps → fee math), pings your phone only when est. profit ≥ $25. | PC, always on |
| **Tailscale** | Makes the website reachable from your phone anywhere, privately. | PC + phone |
| **ntfy** | Free push notifications to your phone. | phone |

## Step 0 — Prerequisites (15 min)

1. Install **Node.js LTS**: https://nodejs.org (defaults are fine).
2. Make sure **Google Chrome** is installed.
3. Get the code onto the PC: `git clone` this repo (branch
   `claude/compounded-interest-game-118ffv`) or GitHub → Code → Download ZIP.
4. **Anthropic API key**: https://console.anthropic.com → API Keys → Create.
   Add $10 credit. Copy the `sk-ant-...` key somewhere handy — you'll paste it
   twice below. (Runs a few cents per appraisal; expect low single-digit
   dollars per day with default settings.)
5. **Tailscale** (free): install on the PC from https://tailscale.com/download,
   sign in (Google login is fine). Install the Tailscale app on your phone,
   sign into the **same** account. That's it — no other config.
6. **ntfy** on your phone: install the ntfy app (App Store / Play Store).
   In the app: Subscribe to topic → invent a long random name like
   `flipwatch-hx83k2p9-newbern` → save it. You'll paste this name below.

## Step 1 — PriceLens server (10 min)

```bat
cd pricelens
npm install
node server.js
```

- First run downloads Playwright bits; let it finish.
- The console prints your **Tailscale URL** like `http://100.x.y.z:8484` —
  **open it on your phone and Add to Home Screen.** That's your app now.
- On the site: tap **API key** (top right) → paste your `sk-ant-...` key.
- **Test it**: snap a photo of anything branded on your desk → you should get
  a verdict card with "real eBay sold data" and a max buy price. If comps come
  back empty repeatedly, stop the server and rerun as `HEADED=1 node server.js`.

## Step 2 — Facebook saved searches sanity check (5 min)

FlipWatch reads search URLs from its config. The defaults target New Bern and
include wide nets (vintage / antique / lot / estate). Optional but recommended:
in your own browser, run one Marketplace search, set radius ~40 miles, copy the
URL, and compare with the config entries — adjust the config URLs if your
Marketplace location slug differs. (This is also where you can add whole
category feeds: browse a category sorted by newest, copy the URL in.)

## Step 3 — FlipWatch (10 min)

```bat
cd flipwatch
npm install
copy config.example.json config.json
notepad config.json
```

In `config.json` set:
- `ntfyTopic`: your topic name from Step 0.6
- `anthropicApiKey`: your `sk-ant-...` key
- leave `compsUrl`, `minProfit` (25), `maxAppraisalsPerCycle` (40) as-is

Then:

```bat
node watch.js
```

- A Chrome window opens → **log into Facebook in it** (your main account, the
  one in good standing). One-time; it stays logged in.
- First sweep seeds silently (no notification flood). From the second sweep on,
  profitable finds ping your phone and appear in the site's **Deals** tab.
- Leave both windows running, minimized. Done.

## Daily operation

- Both terminals stay running on the PC (`pricelens` + `flipwatch`). If the PC
  reboots, restart both: `node server.js` and `node watch.js`.
- Phone buzzes with `+$42 est: ...` → tap → listing opens → message "Is this
  available? Can pick up today, cash" → check the photos against the numbers →
  buy at or under the max, or walk.
- **Deals tab** on your site = everything it found while you weren't looking.
- Out sourcing: **Appraise tab** = point camera at item → verdict + max buy.

## Tuning after a few days

| Symptom | Fix |
|---|---|
| Too many marginal pings | Raise `minProfit` in config.json |
| Too quiet | Lower `minProfit`; add more wide-net searches |
| "appraisal budget exhausted" in console | Raise `maxAppraisalsPerCycle`, or tighten nets' `maxPrice` |
| API spend too high | `"model": "claude-haiku-4-5"` in config.json (~5x cheaper triage) |
| eBay comps empty | Rerun server with `HEADED=1` |
| Facebook logged the watcher out | Log in again in its Chrome window (it pings you when this happens) |

## Standing cautions (same as always)

- FlipWatch automates your logged-in Facebook account gently, but it's still
  against FB's terms — human-paced by design, but not zero risk. Don't speed up
  the intervals, don't add auto-reply.
- Profit estimates assume the item matches its listing. Photos and in-person
  condition checks are still your job.
- The ⅓ rule protects the bankroll: never pay more than a third of expected net.
