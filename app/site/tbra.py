from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from datetime import datetime
import pandas as pd

def get_event_list(config):

    url = config["url"]

    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/chromium"
    chrome_options.add_argument("--headless")  # run headless
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # driver = webdriver.Chrome(
    #     service=Service(ChromeDriverManager().install()), options=chrome_options
    # )
    driver = webdriver.Chrome(
        service=Service("/usr/bin/chromedriver"), options=chrome_options
    )

    driver.get(url)

    # Wait for JS to load
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    event_divs = soup.select("div.SFevtcal")
    events = []

    calendar_filter = config.get("calendar_filter", [])

    for div in event_divs:
        a_tag = div.find("a", class_="SFevt")
        if not a_tag:
            continue  # skip empty days

        try:
            title = a_tag.get("data-ttl", "").strip()
            url = a_tag.get("href", "").strip()
            start_ts = int(a_tag.get("num-sdp", "0"))
            end_ts = int(a_tag.get("num-edp", "0"))
            num_cal = a_tag.get("num-cal", "").strip()

            # Convert timestamps to datetime
            start_dt = datetime.fromtimestamp(start_ts)
            end_dt = datetime.fromtimestamp(end_ts)

            # Apply calendar filter
            if calendar_filter and num_cal in calendar_filter:
                print(f"[INFO] Skipping event Broker Zoom: {url}")
                return None

            events.append(
                {
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                    "Event Title": title,
                    "Event Link": url,
                    "Organizer": config["organizer"],
                    "Industry": config["industry"],
                    "Market": config["market"],
                }
            )

        except Exception as e:
            print(f"[ERROR] Skipping one event block due to error: {e}")
            continue

    time.sleep(config.get("scraper_interval", 1))

    return events


def process(config):
    event_list = get_event_list(config)
    if not event_list:
        print("[INFO] No events found.")
        return []

    df = pd.DataFrame(event_list)
    print(df.to_string(index=False))
    return event_list
