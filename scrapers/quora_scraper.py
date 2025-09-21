import asyncio
import time
from typing import List
from copy import deepcopy

from playwright.async_api import async_playwright
from common.browser_manager import get_browser
from common.db_utils import SCHEMA
from common.anti_detection import goto_resilient, create_stealth_context
from scraper_types import quora_scraper_meta, quora_scraper_visual_text


# Alias Map for Quora
QUORA_ALIAS = {
    "url": ["quora_link", "url"],
    "profile.username": ["username"],
    "profile.full_name": ["title", "full_name"],
    "profile.bio": ["description", "bio"],
    "contact.emails": ["emails"],
    "contact.phone_numbers": ["phones"],
    "contact.websites": ["external_links"],
}


def _map_to_schema(raw: dict, schema: dict = SCHEMA, alias: dict = QUORA_ALIAS) -> dict:
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
    return mapped


async def main(urls: List[str], headless: bool = True) -> List[dict]:
    print(f"--- Starting combined Quora scrape for {len(urls)} URLs ---")

    async with async_playwright() as p:
        browser = await get_browser(p, headless=headless)
        context = await create_stealth_context(browser)
        page = await context.new_page()

        # Meta scrape
        meta_results = await quora_scraper_meta.scrape_quora_meta_seq(urls, page)

        # Visual scrape
        visual_results = await quora_scraper_visual_text.scrape_quora_visible_text_seq(urls, page)

        # Merge
        print("--- Merging Quora results ---")
        merged = {item["quora_link"]: item for item in meta_results}
        for v in visual_results:
            merged[v["quora_link"]] = {**merged.get(v["quora_link"], {}), **v}

        # Map to schema
        print("--- Mapping results into schema ---")
        schema_mapped = [_map_to_schema(v) for v in merged.values()]

        await browser.close()

    return schema_mapped
