import re
import time
from typing import Dict, List, Optional
from playwright.async_api import Page
from common.anti_detection import goto_resilient


def _dedupe(seq: List[str]) -> List[str]:
    seen, out = set(), []
    for s in seq:
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _contacts(text: Optional[str]) -> Dict[str, List[str]]:
    if not text:
        return {"emails": [], "phones": []}
    emails = list({m.group(0) for m in re.finditer(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)})
    phones = list({m.group(0) for m in re.finditer(r"\+?\d[\d\s().\-]{8,}\d", text)})
    return {"emails": emails, "phones": phones}


def _external_links_from_hrefs(hrefs: List[str]) -> List[str]:
    out = [h for h in hrefs if h and h.startswith("http") and "quora.com" not in h]
    return _dedupe(out)[:20]


def _guess_type(url: str) -> str:
    return "profile" if "/profile/" in url.lower() else "question"


async def _extract_page_meta_data(page: Page, url: str) -> Dict:
    page_type = _guess_type(url)
    title = await page.title()
    description = None
    href_nodes = await page.query_selector_all("a[href]")
    hrefs = [await a.get_attribute("href") for a in href_nodes]
    external_links = _external_links_from_hrefs(hrefs)
    text_blob = " ".join(filter(None, [title, description]))
    contact_info = _contacts(text_blob)
    return {
        "platform": "quora",
        "quora_link": url,
        "source": "quora-scraper",
        "type": page_type,
        "title": title,
        "description": description,
        "external_links": external_links,
        "emails": contact_info["emails"],
        "phones": contact_info["phones"],
        "scraped_at": int(time.time()),
    }


async def scrape_quora_meta_seq(urls: List[str], page: Page) -> List[Dict]:
    results = []
    for url in _dedupe(urls):
        try:
            await goto_resilient(page, url)  # ✅ anti-detection nav
            item = await _extract_page_meta_data(page, url)
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
