import asyncio
from playwright.async_api import async_playwright
from scraper_types import quora_scraper_meta, quora_scraper_visual_text


def _merge_results(meta_results, visual_results):
    """
    Merge meta and visible-text results.
    Prefer visible-text values when present (overwrite meta).
    Standardize schema with source='quora'.
    """
    merged = {}
    for item in meta_results + visual_results:
        url = item.get("quora_link")
        if not url:
            continue
        if url not in merged:
            merged[url] = {}
        merged[url].update(item)

        # Standardize schema
        merged[url]["platform"] = "quora"
        merged[url]["source"] = "quora"

    return list(merged.values())


async def _scrape_meta(urls, page):
    """Run the meta scraper using a shared Playwright page."""
    return await quora_scraper_meta.scrape_quora_meta_seq(urls, page)


async def _scrape_visual(urls, page):
    """Run the visual text scraper using a shared Playwright page."""
    return await quora_scraper_visual_text.scrape_quora_visible_text_seq(urls, page)


async def main(urls, headless=True):
    """
    Combined Quora scraper that runs both meta and visual text scrapers,
    then merges their results into a single list.
    """
    print(f"--- Starting combined Quora scrape for {len(urls)} URLs ---")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        page = await browser.new_page()
        try:
            # Run both scrapers with the same page
            meta_results = await _scrape_meta(urls, page)
            visual_results = await _scrape_visual(urls, page)
        finally:
            await browser.close()

    # Merge results into standardized schema
    combined_results = _merge_results(meta_results, visual_results)

    print(f"--- Finished Quora scrape: {len(combined_results)} results ---")
    return combined_results
