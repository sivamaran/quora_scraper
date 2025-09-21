# scraper_types/quora_scraper_visual_text.py (FINAL WITH PROFILE STATS)
import re
import time
from typing import Dict, List, Optional
from playwright.async_api import Page


# ----------------- Helpers -----------------
def _dedupe(seq: List[str]) -> List[str]:
    seen, out = set(), []
    for s in seq:
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _contacts(text: str) -> Dict[str, List[str]]:
    emails = list({m.group(0) for m in re.finditer(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)})
    phones = list({m.group(0) for m in re.finditer(r"\+?\d[\d\s().\-]{8,}\d", text)})
    return {"emails": emails, "phones": phones}


def _external_links_from_hrefs(hrefs: List[str]) -> List[str]:
    """
    Extract only true external links (exclude Quora internal links).
    """
    out = [
        h for h in hrefs
        if h
        and h.startswith("http")
        and "quora.com" not in h.lower()
        and "quorablog.quora.com" not in h.lower()
    ]
    return _dedupe(out)[:20]


def _extract_number(text: Optional[str]) -> Optional[int]:
    """Helper to turn '545,374 followers' -> 545374"""
    if not text:
        return None
    nums = re.findall(r"[\d,]+", text)
    if not nums:
        return None
    return int(nums[0].replace(",", ""))


# ----------------- Main Extraction -----------------
async def scrape_quora_visible_text_seq(urls: List[str], page: Page) -> List[Dict]:
    """
    Extracts visible text (bio, description, stats) from Quora profiles/questions.
    """
    results = []
    for url in _dedupe(urls):
        item = {"platform": "quora", "quora_link": url, "source": "quora"}
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Title / Name
            title_el = await page.query_selector("h1, h2, .q-text")
            title = await title_el.inner_text() if title_el else None

            # Bio / Description
            desc_el = await page.query_selector(".q-text.qu-dynamicFontSize--small, .q-relative")
            description = await desc_el.inner_text() if desc_el else None

            # Followers
            followers_el = await page.query_selector("a[href*='followers'] .q-text, .q-box:has-text('Followers')")
            followers_text = await followers_el.inner_text() if followers_el else None
            followers = _extract_number(followers_text)

            # Following
            following_el = await page.query_selector("a[href*='following'] .q-text, .q-box:has-text('Following')")
            following_text = await following_el.inner_text() if following_el else None
            following = _extract_number(following_text)

            # Answers count
            answers_el = await page.query_selector("a[href*='answers'] .q-text, .q-box:has-text('Answers')")
            answers_text = await answers_el.inner_text() if answers_el else None
            answers_count = _extract_number(answers_text)

            # Questions count
            questions_el = await page.query_selector("a[href*='questions'] .q-text, .q-box:has-text('Questions')")
            questions_text = await questions_el.inner_text() if questions_el else None
            questions_count = _extract_number(questions_text)

            # Links
            href_nodes = await page.query_selector_all("a[href]")
            hrefs = [await a.get_attribute("href") for a in href_nodes]
            external_links = _external_links_from_hrefs(hrefs)

            # Contact info (regex from bio + title)
            text_blob = " ".join(filter(None, [title, description]))
            contact_info = _contacts(text_blob)

            item.update({
                "type": "profile" if "/profile/" in url.lower() else "question",
                "title": title,
                "description": description,
                "followers": followers,
                "following": following,
                "answers_count": answers_count,
                "questions_count": questions_count,
                "external_links": external_links,
                "emails": contact_info["emails"],
                "phones": contact_info["phones"],
                "scraped_at": int(time.time())
            })
        except Exception as e:
            item.update({
                "error": f"{e.__class__.__name__}: {str(e)}",
                "scraped_at": int(time.time())
            })

        results.append(item)
    return results
