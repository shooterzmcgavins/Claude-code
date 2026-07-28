# PriceLens

Snap a photo of an item → AI identifies it → **real eBay sold-listing comps**
pulled through a browser on your PC → fee math → verdict with a **max buy
price** (the ⅓-of-net rule). Built for thrift stores, estate sales, and
Marketplace scrolling.

Two pieces:

- `server.js` runs on your PC. It serves the app and exposes `/comps`, which
  opens eBay's public sold-listings search in a local browser (no eBay login,
  no eBay account involved), parses the sold prices, and caches them for a day.
  Requests are queued and spaced ~5s apart so usage looks like a person browsing.
- `index.html` is the app. It sends your photo to Claude for identification,
  asks the server for real comps on the identified item, and computes fees,
  net, and max-buy locally. If the server can't find comps (or you open the
  file without the server), it falls back to a Claude web-search estimate —
  the card is labeled **"real eBay sold data"** vs **"web-search estimate"**
  so you always know which you're looking at.

## Setup (~10 minutes)

1. **Get an Anthropic API key**: [console.anthropic.com](https://console.anthropic.com)
   → API keys → Create key. Add $5–10 of credit — identification costs a few
   cents per photo (comps come from your own PC, free).
2. **Start the server** (same prerequisites as FlipWatch — Node.js + Chrome):

   ```
   cd pricelens
   npm install
   node server.js
   ```

3. **Open the app**: `http://localhost:8484` on the PC. From your phone:
   - **at home**: `http://<your-pc's-local-ip>:8484` (same wifi; find the IP
     with `ipconfig` — the 192.168.x.x one)
   - **out sourcing**: install [Tailscale](https://tailscale.com) (free) on the
     PC and phone — then the same URL with the PC's Tailscale IP works from
     anywhere, thrift store included, as long as the PC is on.
4. Tap **API key** (top right), paste your key, save.

If comps come back empty repeatedly, eBay may be soft-blocking headless
browsing — restart the server with `HEADED=1 node server.js` to use a visible
browser window, which usually resolves it.

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
