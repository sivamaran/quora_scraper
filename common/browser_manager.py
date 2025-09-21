# common/browser_manager.py

from playwright.async_api import Playwright, Browser, Page
from .anti_detection import goto_resilient, create_stealth_context


async def get_browser(playwright: Playwright, headless: bool = True) -> Browser:
    """
    Launches and returns a stealthy browser instance.
    """
    browser = await playwright.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-infobars",
            "--disable-extensions",
        ],
    )
    return browser


async def get_stealth_page(browser: Browser) -> Page:
    """
    Creates a new stealth context + page.
    """
    context = await create_stealth_context(browser)
    page = await context.new_page()
    return page
