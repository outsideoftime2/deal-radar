# Black Friday Deal Radar

A phone-friendly, static GitHub Pages site for Knoxville, TN, Tyler, TX, and Tucson, AZ. Includes a glowing SCAN button, swipeable cards, list mode, retailer/date/category filters, and retailer verification links.

## Publish for your family

1. Create a **public** GitHub repository (for example `deal-radar`). Upload **all files and the `.github/workflows/scan.yml` folder**, preserving paths.
2. In **Settings → Pages**, choose **Deploy from a branch**, `main`, `/ (root)`, and save. GitHub provides a shareable `https://USERNAME.github.io/deal-radar/` URL.
3. In **Actions**, run **Refresh deal feed** using **Run workflow**. It is also scheduled four times a day during November and December (UTC).
4. Open the Pages URL on a phone. Add it to the home screen if desired.

## Important: deal completeness

**This is a functional site and collection framework, not a complete live scraper of three retail catalogs.** `sources.json` starts empty because there is no established, authorized comprehensive feed for Target, Kohl's and Walmart. It would be misleading to pre-populate made-up prices or label ordinary product prices as Black Friday offers. Scheduled runs initially publish **zero verified deals** and explicitly report coverage. A browser-only HTML file cannot access blocked retailer sites directly.

### Connect real deal sources

- `sources.json`: add **permitted public HTTPS product URLs** to each retailer's array. The collector reads JSON-LD Product/Offer data, but publishes only offers with **explicit `validFrom` and `priceValidUntil` dates and a price**. Many retailer pages omit these fields, in which case no deal is published. It does not circumvent login, anti-bot restrictions, or rate limits.
- `manual_deals.json`: optionally add records verified against official retailer offers. Each record needs `id`, `retailer` (`target`, `kohls`, `walmart`), `title`, `description`, `category`, `sale_price`, `regular_price` (or `null`), `start_date` and `end_date` (`YYYY-MM-DD`), `url` (on that retailer's domain), `cities` (`["all"]`, `["knoxville"]`, `["tyler"]`, `["tucson"]`, or any combination), `availability`, `verified: true`, and `verified_at` (ISO 8601 with timezone). The collector automatically excludes records verified more than 72 hours ago and expired deals.
- A truly **comprehensive** service requires a retailer-approved product/promotions feed or a licensed data provider, potentially at a cost. In-store stock and city-specific prices require a source that explicitly supports store IDs or ZIP codes. This template does not falsely infer city availability.

## Test locally

Run `python collector.py` and `python -m http.server 8000` from this folder, then open `http://localhost:8000`. Opening `index.html` via `file://` often blocks the JSON fetch; use GitHub Pages or a local server.

## Notes

The `SCAN DEALS` button refreshes the latest **published** `deals.json` file, not a live request to each retailer. GitHub Actions performs the background collection. Scheduled GitHub workflows may run late or be disabled after repository inactivity. The site exposes coverage state so missing deals are not represented as zero deals. Confirm all prices, dates and local inventory at the retailer before purchasing.
