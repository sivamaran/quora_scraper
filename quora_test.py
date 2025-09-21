import asyncio
import json
import os
import sys

# --- Path setup to allow importing from the 'scrapers' package ---
# It assumes this test script is run from the project's root directory.
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the main Quora scraper
from scrapers.quora_scraper import main as run_quora_scraper


async def run_test():
    """
    Reads URLs from 'quora_urls.txt', runs the main scraper,
    and saves the output to 'quora_output.json'.
    """
    # Paths (adjusted to match your repo structure)
    urls_file_path = os.path.join(project_root, 'quora_urls.txt')
    output_file_path = os.path.join(project_root, 'quora_output.json')

    print(f"--- Running Quora Scraper Test ---")

    # Read the URLs from the test file
    try:
        with open(urls_file_path, 'r', encoding='utf-8') as f:
            test_urls = [line.strip() for line in f if line.strip()]
        print(f"Found {len(test_urls)} URLs in '{os.path.basename(urls_file_path)}'")
    except FileNotFoundError:
        print(f"Error: Test URLs file not found at '{urls_file_path}'")
        return

    if not test_urls:
        print("No URLs found in the test file. Exiting.")
        return

    # Run the main scraper function with the test URLs
    results = await run_quora_scraper(test_urls, headless=True)

    # Save the results to the specified output file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n--- Test Complete ---")
    print(f"Results have been saved to '{output_file_path}'")


if __name__ == "__main__":
    # Use asyncio.run() to execute the async run_test function
    asyncio.run(run_test())
