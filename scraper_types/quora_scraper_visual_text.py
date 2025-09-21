# scraper_types/quora_scraper_visible_text.py (FINAL REFACTORED VERSION)
import re
import json
import time
import asyncio
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from playwright.async_api import Page, TimeoutError

# --- All of your original helper functions are kept ---
def _norm(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()

def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen, out = set(), []
    for x in items:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out

def _split_quora_links(links: List[str]) -> Tuple[List[str], List[str]]:
    externals, quoras = [], []
    for href in links:
        try:
            if not href.startswith("http"):
                full_href = f"https://www.quora.com{href}"
                quoras.append(full_href)
                continue
            u = urlparse(href)
            host = (u.netloc or "").lower()
            if "quora.com" in host:
                quoras.append(href)
            else:
                cleaned = f"{u.scheme}://{u.netloc}{u.path}" if u.scheme else href
                externals.append(cleaned.rstrip("/"))
        except Exception:
             if "quora.com" in href: quoras.append(href)
             else: externals.append(href)
    return _dedupe_keep_order(externals), _dedupe_keep_order(quoras)

EMAIL_RE = re.compile(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", re.I)
PHONE_RE = re.compile(r"(\+?\d{1,3})?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")

def _extract_entities_from_text(text: str) -> Dict[str, List[str]]:
    return {
        "emails": _dedupe_keep_order(EMAIL_RE.findall(text)),
        "phones": _dedupe_keep_order(PHONE_RE.findall(text)),
    }

async def _click_expanders(page: Page) -> None:
    for _ in range(10):
        any_clicked = False
        expand_buttons = page.locator('button:has-text("more")')
        count = await expand_buttons.count()
        if count == 0: break
        for i in range(count):
            try:
                button = expand_buttons.nth(i)
                if await button.is_visible():
                    await button.click()
                    any_clicked = True
                    await page.wait_for_timeout(500)
            except Exception:
                pass
        if not any_clicked:
            break

# --- Your original data extraction function is kept ---
async def extract_visible_text_from_quora_page(page: Page) -> Dict:
    for _ in range(5):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
    await _click_expanders(page)
    question_title = ""
    try:
        title_locator = page.locator('div[data-testid="QuestionPage-Question-title"] span.qu-bold').first
        question_title = _norm(await title_locator.inner_text())
    except Exception:
        question_title = "Title not found"
    answers_text, answer_authors = [], []
    answer_blocks = page.locator('div[data-testid^="Answer-TopLevel"]')
    for i in range(await answer_blocks.count()):
        block = answer_blocks.nth(i)
        try:
            text_content = _norm(await block.locator('div[data-testid="Answer-body-text"]').inner_text())
            if text_content: answers_text.append(text_content)
            author_name = _norm(await block.locator('a[href*="/profile/"]').first.inner_text())
            if author_name: answer_authors.append(author_name)
        except Exception:
            continue
    full_text = question_title + "\n\n" + "\n\n".join(answers_text)
    raw_links = [await a.get_attribute("href") for a in await page.locator('a[href]').all()]
    external_links, quora_links = _split_quora_links(_dedupe_keep_order(raw_links))
    entities = _extract_entities_from_text(full_text)
    return {
        "question_title": question_title or None, "text": full_text,
        "external_links": external_links, "quora_links": quora_links,
        "answer_authors": _dedupe_keep_order(answer_authors),
        "emails": entities["emails"], "phones": entities["phones"],
    }

# --- This is the new, refactored main function ---
async def scrape_quora_visible_text_seq(urls: List[str], page: Page) -> List[Dict]:
    """
    Sequentially scrapes Quora URLs using a PRE-CONFIGURED page object.
    """
    results = []
    for url in urls:
        item = {"platform": "quora", "quora_link": url, "scraped_at": int(time.time())}
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_selector('div[id*="mainContent"]', timeout=20000)
            try:
                close_button = page.locator('button[aria-label="Close"], [aria-label="Close dialog"]').first
                if await close_button.is_visible(timeout=5000):
                    await close_button.click()
            except (TimeoutError, Exception):
                pass
            extracted = await extract_visible_text_from_quora_page(page)
            item.update(extracted)
        except Exception as e:
            item["error"] = str(e)
        results.append(item)
    return results