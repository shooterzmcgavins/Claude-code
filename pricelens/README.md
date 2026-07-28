# PriceLens

Snap a photo of an item → AI identifies it, searches recent **sold** prices on
the live web, applies platform fees, and gives you a verdict with a **max buy
price** (the ⅓-of-net rule). Built for thrift stores, estate sales, and
Marketplace scrolling.

One file, no build, no server. The app calls the Anthropic API directly from
your browser; your API key is stored only in your browser's localStorage and is
sent nowhere except api.anthropic.com.

## Setup (~5 minutes)

1. **Get an Anthropic API key**: [console.anthropic.com](https://console.anthropic.com)
   → API keys → Create key. Add $5–10 of credit — each appraisal costs roughly
   **5–15 cents** (one Claude Opus call with vision + a few web searches).
2. **Open the app**: open `index.html` in any browser. To use it on your phone
   (where it shines), either:
   - host this folder anywhere static (GitHub Pages: repo Settings → Pages →
     deploy from branch — then visit `https://<you>.github.io/<repo>/pricelens/`), or
   - email/AirDrop the file to your phone and open it in the browser.
3. Tap **API key** (top right), paste your key, save.

## Using it

1. In the aisle: tap the photo zone → snap the item. Get the maker's mark or
   model number in frame if you can.
2. Optionally type a note: brand/model if you know it, condition, and the
   asking price ("Penn 704Z, they want $15").
3. Tap **What's it worth?** — 15–60 seconds later you get:
   - **GRAB / MAYBE / PASS** verdict
   - recent sold price range (from live web search, not asking prices)
   - best platform to sell on and the fee math
   - **max buy price** — never pay more than this

Photos are downscaled to ~1200px before upload to keep per-call token cost low.

## Notes

- The verdict is an estimate from web comps — condition quirks the photo hides
  (cracks, missing parts, repro tells) are on you to check in person.
- If identification confidence is "low", treat it as a MAYBE regardless of the
  numbers, or send the photo to Claude chat for a closer look.
- Troubleshooting: a 401 error means the key is wrong; "Failed to fetch"
  usually means no network. Costs show up in your Anthropic console under Usage.
