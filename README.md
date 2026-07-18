# Zyn Log

A dead-simple, private app to log your Zyn (nicotine pouch) use. One tap per pouch — that's the whole idea. Watching the daily count is often enough to bring it down.

- **One tap to log a pouch.** Big count of how many you've had today.
- **Nicotine (and optional cost) tally** for today, right under the count. Defaults to 3 mg per pouch; set a price to also see money spent (leave it blank to hide cost).
- **Quit forecast.** Projects when you'll hit zero by fitting a line to your recent daily counts and finding where the downward trend reaches 0/day. Shows the date, how far off it is, and your reduction pace — and honestly says "no downward trend yet" when your counts aren't actually falling.
- **Today's list** with timestamps, and a remove button on each.
- **Last 7 days** at a glance, so you can see the trend.
- **100% private.** Data is stored locally in your browser (`localStorage`). No account, no server, nothing uploaded.

## How to use it

1. Open `index.html` in any browser.
2. On your phone, open it and **Add to Home Screen** so logging is one tap.
3. Tap **+ Log a pouch** each time you use one.

Desktop shortcuts: `L` to log, `Z` to undo. Use **Export** (at the bottom) to back up your data.

## Tech

Single self-contained `index.html` — no build step, no dependencies, works offline.
