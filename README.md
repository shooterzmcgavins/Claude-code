# 🚭 Quit Zyn — Nicotine Tracker

A tiny, private app to track your Zyn (nicotine pouch) use and taper off it for good.

- **One tap to log a pouch.** See how many you've had today vs. your limit.
- **Automatic step-down plan.** Your daily limit drops by 1 every few days until you reach your target (default: quit). No willpower math required.
- **Streaks & trends.** A running streak of days at/under your limit, a 7-day average, and a 14-day bar chart.
- **Motivation that's real.** Live totals for money saved and nicotine avoided vs. your starting baseline.
- **100% private.** All data is stored locally in your browser (`localStorage`). Nothing is uploaded, no account, no server.

## How to use it

1. Open `index.html` in any browser (double-click it, or host it anywhere).
2. On your phone, open it and **Add to Home Screen** so logging is one tap.
3. Tap **+ Log a pouch** every time you use one. That's it.
4. Open **⚙︎ Settings** to set your baseline, target limit, step-down speed, nicotine per pouch (mg), and price per pouch.

### Tips
- Keyboard shortcuts on desktop: `L` to log a pouch, `Z` to undo.
- Use **Export data** in settings to back up, and **Import** to restore or move to a new device.

## The step-down plan

Set a **baseline** (what you're using now) and a **target limit** (0 = fully quit).
Choose how fast to taper — e.g. "reduce by 1 every 3 days." The app lowers your
daily limit automatically over time and never drops below your target. Ride out
each craving; they usually pass in a few minutes. You've got this. 💪

## Tech

Single self-contained `index.html` — no build step, no dependencies, works offline.
