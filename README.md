# Daily Tracker

A private, MyFitnessPal-style daily tracker for the things you want to keep an eye on — food (calories + macros), nicotine, water, coffee, weight, and anything else you add. Light theme, blue accent, circular progress rings, and a meal-based food diary. One file, no accounts, no server; all data stays in your browser on your device.

The Food card is a full diary: a calories-remaining ring, carb/protein/fat rings, and Breakfast / Lunch / Dinner / Snacks sections you add foods into.

## What it tracks

- **Zyn** — one-tap pouch logging with a nicotine (and optional cost) tally and a **quit forecast** that projects your zero date from your trend.
- **Water** — enter an amount in ounces (quick buttons or type any number) toward a bodyweight-based daily goal.
- **Coffee** — tap to count cups against a daily limit.
- **Food** — search for a food and pick servings; **calories and macros (protein / carbs / fat) fill in automatically**. Uses a built-in library of ~120 common whole foods (works offline) plus live results from the online [Open Food Facts](https://world.openfoodfacts.org/) database (millions of packaged/branded products; needs a connection). Manual entry is available as a fallback.
- **Weight** — log a daily weigh-in and watch the trend.
- **Custom trackers** — add your own (steps, vitamins, workouts, mood…) as a tap-counter, a daily number, or a food-style tracker, each with its own icon and goal.

Every tracker shows today's value, progress toward its goal, a 7-day sparkline, and an expandable list of entries and recent days. Tap the ⚙︎ on a card to edit goals, units, or delete it.

## How to use it

1. Open `index.html` in any browser (or the hosted URL).
2. On your phone, open it and **Add to Home Screen** for one-tap access.
3. Tap **+** on a card to log; tap **+ Food** / **Log** for food and weight; tap **＋ Add a tracker** to make your own.

Use **Export** to back up your data to a file and **Import** to restore it (handy before clearing your browser or switching devices).

## Privacy

All data is stored locally in your browser (`localStorage`). Nothing is uploaded, there are no accounts, and it works offline.

## Tech

Single self-contained `index.html` — no build step, no dependencies.
