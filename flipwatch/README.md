# FlipWatch

A local Facebook Marketplace watcher. It opens a real Chrome window on **your**
PC with **your** login, re-checks your searches every few minutes like a
patient human would, and pushes an instant notification to your phone the
moment a new listing appears. Tap the notification → the listing opens in the
Facebook app → hit Facebook's own "Is this available?" button. You can be the
first responder within a minute of a listing going live.

What it deliberately does **not** do:

- **No auto-replies.** A bot messaging sellers as you is the fastest way to
  get banned, and it commits you to deals sight-unseen. You reply with one tap.
- **No headless mode, no proxies, no fingerprint tricks.** It's a visible
  browser refreshing pages at a human pace during waking hours.

**Honest risk note:** any automation of a logged-in Facebook account is
against Facebook's Terms of Service. FlipWatch is built to be as gentle and
human-shaped as possible (visible browser, minutes between visits, random
timing, nightly quiet hours), but the risk of a checkpoint or suspension is
never zero. Run it on an account you're willing to risk, keep the interval at
5 minutes or slower, and don't add more than ~8 searches.

## Setup (once, ~15 minutes)

### 1. Install Node.js
Download the LTS installer from <https://nodejs.org> and run it.

### 2. Get this folder onto your PC
Clone the repo or just copy the `flipwatch/` folder somewhere like
`C:\flipwatch`.

### 3. Install dependencies
Open a terminal (Windows: press Start, type `cmd`) and run:

```
cd C:\flipwatch
npm install
```

FlipWatch drives your installed Google Chrome. If you don't have Chrome,
install it, or run `npx playwright install chromium` and change
`channel: "chrome"` to nothing in `watch.js`.

### 4. Set up phone notifications (free, no account)
1. Install the **ntfy** app ([Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / [iOS](https://apps.apple.com/us/app/ntfy/id1625396347)).
2. In the app, subscribe to a topic with a long random name you invent,
   e.g. `flipwatch-hx83k2p9-newbern`. The name is the only security — make it
   unguessable.
3. Put that same topic name in `config.json` as `ntfyTopic`.

### 5. Configure your searches
Copy `config.example.json` to `config.json`. For each search:

1. In your normal browser, go to Facebook Marketplace and build the search you
   want — keywords, price cap, radius (set it to ~40 miles), and set
   **Date listed: last 24 hours**.
2. Copy the URL from the address bar into the `url` field.
3. `maxPrice` (optional) filters out anything above that price.
4. Keep `intervalMinutes` at 5 or higher.

### 6. First run
```
node watch.js
```

A Chrome window opens. Log into Facebook in it (this login is saved in the
local `fb-profile` folder — you only do it once). The first sweep records
what's already listed without notifying; alerts start on the next cycle.
Leave the window open and minimized.

## Smart mode: only ping when it's profitable

With `anthropicApiKey` set in `config.json` (and the PriceLens comps server
running — see `../pricelens/README.md`), FlipWatch appraises every new listing
before deciding whether to buzz you:

1. Claude reads the listing title + asking price and works out the exact eBay
   sold-listings search for the item (or skips listings too generic to identify).
2. The PriceLens server pulls **real eBay sold comps** for it.
3. Fee math runs; if estimated profit (median sold − fees − shipping − asking
   price) clears `minProfit` (default $25), your phone buzzes with the numbers:
   `+$42 est: Penn 704Z Spinfisher — Ask $15 · sells ~$70 (23 eBay solds)`.
4. Everything else is logged to the console but stays silent.

Tuning: raise `minProfit` if you're getting too many marginal pings; lower it
(or delete `anthropicApiKey` to return to raw-ping mode) if it's too quiet.
Each appraisal costs a few cents of API credit; comps are free from your own
PC and cached for a day. If the API or comps server is down, FlipWatch fails
open — it pings the raw listing rather than silently dropping a possible deal.

Two caveats worth knowing:
- The check runs on the listing **title only** (FlipWatch deliberately doesn't
  open every listing page — that would multiply its Facebook footprint). A
  vague title on a great item ("old fishing reel $10") gets skipped. Your eyes
  on Marketplace push notifications still catch those.
- Estimated profit assumes the item matches its title and is in sellable
  condition. Tap through and check photos before driving anywhere.

## Using it

- **Notification arrives** → tap it → listing opens → tap Facebook's
  "Is this available?" to claim your place in line, then check the photos
  against the numbers in the ping.
- The golden rule still applies: never pay more than **1/3 of expected net
  resale**. Claim first, verify condition second, walk away freely.

## Troubleshooting

- **"FlipWatch needs you to log in" notification** — Facebook logged the
  watcher out. Open its Chrome window and sign in again.
- **No notifications but the console shows "0 new"** — normal; it only pings
  for listings it hasn't seen before.
- **Selectors break / no listings found ever** — Facebook changed their page
  markup. Tell Claude and get an updated `watch.js`.
- **Stop it** — close the terminal window or press Ctrl+C.
