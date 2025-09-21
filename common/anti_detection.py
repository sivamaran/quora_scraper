import asyncio
import random
from playwright.async_api import TimeoutError as PlaywrightTimeout


async def goto_resilient(page, url: str, retries: int = 3, timeout: int = 30000):
    """
    A resilient navigation method with retries + randomized waits.
    Helps evade bot detection.
    """
    for attempt in range(retries):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            await asyncio.sleep(random.uniform(2, 4))  # simulate human pause
            return
        except PlaywrightTimeout:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"⚠️ Timeout. Retrying in {wait}s... (attempt {attempt+1}/{retries})")
                await asyncio.sleep(wait)
            else:
                raise
        except Exception as e:
            if attempt < retries - 1:
                print(f"⚠️ Error {e}. Retrying... (attempt {attempt+1}/{retries})")
                await asyncio.sleep(2)
            else:
                raise


async def create_stealth_context(browser):
    """
    Creates a browser context with anti-detection measures.
    - Random user agent
    - Disabled automation flags
    - Standard viewport
    """
    user_agent = random.choice([
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36",

        # Safari on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.0 Safari/605.1.15",

        # Chrome on Linux
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36",
    ])

    context = await browser.new_context(
        user_agent=user_agent,
        viewport={
            "width": random.randint(1200, 1400),
            "height": random.randint(700, 900)
        },
        locale="en-US",
        java_script_enabled=True,
    )

    # Hide webdriver flag (common bot detection check)
    await context.add_init_script(
        """Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"""
    )

    return context
