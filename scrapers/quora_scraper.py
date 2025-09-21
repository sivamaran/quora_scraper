import asyncio
import time
from typing import List, Dict
from copy import deepcopy

from playwright.async_api import async_playwright
from common.browser_manager import get_browser
from common.db_utils import SCHEMA
from scraper_types import quora_scraper_meta, quora_scraper_visual_text


# ---------------- Alias Map for Quora ----------------
QUORA_ALIAS = {
    "url": ["quora_link", "url"],
    "profile.username": ["username"],
    "profile.full_name": ["title", "full_name"],
    "profile.bio": ["description", "bio"],
    "contact.emails": ["emails"],
    "contact.phone_numbers": ["phones"],
    "contact.websites": ["external_links"],
    "contact.bio_links": ["external_links"],

    # optional extras if we scrape counts
    "profile.followers": ["followers"],
    "profile.following": ["following"],
    "profile.answers_count": ["answers_count"],
    "profile.questions_count": ["questions_count"],
}


def _map_to_schema(raw: dict, schema: dict = SCHEMA, alias: dict = QUORA_ALIAS) -> dict:
    """Reshape raw scraper dict into SCHEMA format using alias mapping."""
    mapped = deepcopy(schema)

    for schema_key, possible_keys in alias.items():
        target = mapped
        parts = schema_key.split(".")
        for p in parts[:-1]:
            target = target[p]

        for key in possible_keys:
            if key in raw and raw[key]:
                target[parts[-1]] = raw[key]
                break

    # Always enforce platform + source
    mapped["platform"] = "quora"
    mapped["source"] = "quora-scraper"
    mapped["metadata"]["scraped_at"] = raw.get("scraped_at", int(time.time()))

    return mapped


# ---------------- Main Scraper ----------------
async def main(urls: List[str], headless: bool = True) -> List[Dict]:
    """
    Orchestrates Quora scraping using both meta + visible_text scrapers.
    Returns standardized schema results.
    """
    print(f"--- Starting combined Quora scrape for {len(urls)} URLs ---")

    async with async_playwright() as p:
        browser = await get_browser(p, headless=headless)   # ✅ pass playwright
        page = await browser.new_page()

        # Run meta scraper
        #print("--- Running Quora meta scrape ---")
        meta_results = await quora_scraper_meta.scrape_quora_meta_seq(urls, page)

        # Run visible text scraper
        #print("--- Running Quora visible text scrape ---")
        visual_results = await quora_scraper_visual_text.scrape_quora_visible_text_seq(urls, page)

        await browser.close()

    # Merge results
    print("--- Merging Quora results ---")
    merged = {}
    for item in meta_results + visual_results:
        url = item.get("quora_link")
        if not url:
            continue
        if url not in merged:
            merged[url] = {}
        merged[url].update(item)

    # Map into schema
    print("--- Mapping results into schema ---")
    schema_mapped = [_map_to_schema(v) for v in merged.values()]

    print(f"--- Finished Quora scrape: {len(schema_mapped)} results ---")
    return schema_mapped
