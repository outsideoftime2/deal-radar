# Black Friday Deal Radar — free upgrade

This is a complete replacement package for the existing GitHub Pages repository. It preserves the three-city UI and the scheduled workflow, and adds `official_promotions.json` with retailer-announced 2026 Black Friday promotions.

## Install

1. Extract the ZIP.
2. In your existing `deal-radar` GitHub repository, upload/replace `index.html`, `collector.py`, `official_promotions.json`, `sources.json`, `manual_deals.json`, `deals.json` and `.github/workflows/collect-deals.yml`, preserving the workflow folder. Do not upload the ZIP as one file.
3. **Keep your existing `.github/workflows/static.yml` unchanged.** If the repository also contains an older `.github/workflows/scan.yml`, disable or delete that older workflow to avoid redundant scans.
4. Commit changes. Open **Actions → Refresh deal feed → Run workflow** to refresh and deploy. Check the run log and your live site.

## What this does and does not do

- Publishes explicitly dated *retailer-announced promotions* for 2026, even when no individual item price is available. These announcements are sourced from official retailer releases, **not live rechecked** each run.
- Excludes expired promotions automatically. Includes upcoming promotions.
- Optionally extracts products from HTTPS retailer URLs listed in `sources.json` only if pages are accessible and contain explicitly dated JSON-LD Product offers. It does not crawl all products, evade blocks, or infer discounts.
- `manual_deals.json` supports source-linked, recently verified individual deals. This file is empty initially.
- The three cities show nationally announced offers, **not independently verified local inventory or prices**.
- **This is not an exhaustive Black Friday catalog.** Full automatic retailer coverage is not available from these free sources.

## Official announcement sources

- Target (Nov 17): https://corporate.target.com/press/release/2026/11/target-announces-black-friday-deals-and-giveaways-to-help-families-save-big-on-gifts-they-ll-love-to
- Kohl's (Oct 30): https://s204.q4cdn.com/271435555/files/doc_news/Now-Arriving-at-The-North-Kohls-November-Holiday-Savings-Events-2026.pdf
- Walmart: https://corporate.walmart.com/askwalmart/when-are-walmarts-2026-black-friday-and-cyber-monday-deals

## Local test

Run `python collector.py`, then `python -m http.server 8000` and visit http://localhost:8000. Use the SCAN button to refresh `deals.json`.

No third-party packages or API keys required.
