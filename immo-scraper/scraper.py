from datetime import datetime
import json
import logging
from pathlib import Path
from playwright.async_api import async_playwright, Response
from playwright_stealth import stealth_async
from models import Listing, parse_listings


logger = logging.getLogger(__name__)

def get_file_name()->str:
    # Get current date and time
    now = datetime.now()

    # Format as mmhh_DDMMYYYY
    formatted_time = now.strftime("%M%H_%d%m%Y")
    return f"{formatted_time}.json"


async def scrape_immo_webpage(cb: any):
    
    async with async_playwright() as p:
        for browser_type in [p.chromium]:
            browser = await browser_type.launch(headless=True)
            page = await browser.new_page()
            async def intercept_response(response: Response) -> None:
                logger.info(f"{response.url} - {response.status} - {response.ok} - {response.ok and "wohnung-mieten" in response.url}")

                if response.ok and "wohnung-mieten" in response.url:

                    text = await response.text()
                    text = text.split("resultListModel:")[1]
                    text = text.split("isUserLoggedIn")[0].strip()[:-1]
                    file_name = get_file_name()
                    Path(file_name).write_text(text)

                    listings: Listing = parse_listings(json.loads(text))
                    await cb(listings)

            page.on("response", intercept_response)

            await stealth_async(page)
            await page.goto(
                "https://www.immobilienscout24.de/Suche/radius/wohnung-mieten?centerofsearchaddress=M%C3%BCnchen%3B80538%3B%3B%3B%3B%3B&price=-1800.0&livingspace=60.0-&exclusioncriteria=projectlisting,swapflat&pricetype=rentpermonth&geocoordinates=48.14126%3B11.58986%3B5.0&sorting=2"
            )
            await page.wait_for_timeout(100000)
