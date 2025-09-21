import asyncio
from scrapers.quora_scraper import main as run_quora_scraper
from common.db_utils import save_to_mongo, save_to_json


async def run_test():
    urls = [
        "https://www.quora.com/profile/Adam-D-Angelo",
        "https://www.quora.com/profile/Another-Profile"
    ]

    results = await run_quora_scraper(urls, headless=True)  # already schema-mapped

    # Save into MongoDB
    save_to_mongo(results, db_name="leadgen", collection_name="quora_leads")

    # Save into JSON file
    save_to_json(results, output_file="quora_output.json")


if __name__ == "__main__":
    asyncio.run(run_test())
