import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import os

async def download_files():
    # Path to your CSV file
    csv_path = r"C:\Users\Machine81\code\anthropic-quickstarts\computer-use-demo\computer_use_demo\extracted_links.csv"
    
    # Read the CSV file
    df = pd.read_csv(csv_path)

    # Initialize Playwright
    async with async_playwright() as p:
        # Launch Chromium with specified user data directory
        browser = await p.chromium.launch(channel="chrome", headless=False)


        # Open a new page
        page = await browser.new_page()

        base_url = "https://www.autochlor.net/wps/"
        await page.goto(base_url)

        # Directory to save downloads
        download_path = os.path.join(os.getcwd(), "downloads")
        os.makedirs(download_path, exist_ok=True)

        for index, row in df.iterrows():
            if row['url_type'] == 'File':
                file_url = base_url + row['url']
                print(f"Downloading from URL: {file_url}")

                try:
                    # Listen for the download event
                    async with page.expect_download() as download_info:
                        await page.goto(file_url)
                    download = await download_info.value
                    
                    # Save the downloaded file to the specified path
                    await download.save_as(os.path.join(download_path, download.suggested_filename))
                    print(f"Downloaded: {download.suggested_filename}")

                except Exception as e:
                    print(f"Error downloading from URL: {file_url}")
                    print(e)

        # Close the browser after all downloads
        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_files())