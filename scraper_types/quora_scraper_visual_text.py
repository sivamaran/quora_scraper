import time
from typing import List, Dict
from playwright.async_api import Page
from common.anti_detection import goto_resilient


async def _extract_visible_text(page: Page, url: str) -> Dict:
    try:
        name_el = await page.query_selector("h1, h2")
        title = await name_el.inner_text() if name_el else None

        desc_el = await page.query_selector("div, p")
        description = await desc_el.inner_text() if desc_el else None

        return {
            "platform": "quora",
            "quora_link": url,
            "source": "quora-scraper",
            "type": "profile",
            "title": title,
            "description": description,
            "external_links": [],
            "emails": [],
            "phones": [],
            "scraped_at": int(time.time()),
        }
    except Exception as e:
        return {
            "platform": "quora",
            "quora_link": url,
            "source": "quora-scraper",
            "error": f"{e.__class__.__name__}: {str(e)}",
            "scraped_at": int(time.time()),
        }


async def scrape_quora_visible_text_seq(urls: List[str], page: Page) -> List[Dict]:
    results = []
    for url in urls:
        try:
            await goto_resilient(page, url)  # ✅ anti-detection nav
            item = await _extract_visible_text(page, url)
        except Exception as e:
            item = {
                "platform": "quora",
                "quora_link": url,
                "source": "quora-scraper",
                "error": f"{e.__class__.__name__}: {str(e)}",
                "scraped_at": int(time.time()),
            }
        results.append(item)
    return results
