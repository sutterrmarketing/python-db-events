import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time
import random
import pandas as pd
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}

def get_event_list(config):

    time.sleep(config.get("scraper_interval", 1))

    response = requests.get(config["url"], headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")
    blocks = soup.select(config["event_list_selector"])
    events = []

    for block in blocks:
        try:
            title_tag = block.find("h3")
            title = title_tag.get_text(strip=True) if title_tag else None

            date_text = block.select_one(
                "div.col-md-4:nth-of-type(1) div.col-md-11"
            ).get_text(strip=True)
            time_text = block.select_one(
                "div.col-md-4:nth-of-type(2) div.col-md-11"
            ).get_text(strip=True)

            link_tag = block.select_one("a[href*='meetinginfo.php']")
            event_url = (
                urljoin(config["base_url"], link_tag["href"])
                if link_tag
                else config["url"]
            )

            start_dt = datetime.strptime(date_text, "%B %d, %Y")
            start_time, end_time = ["", ""]

            if "to" in time_text:
                start_time, end_time = [t.strip() for t in time_text.split("to")]

            start_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
            end_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
            parsed_start_time = datetime.strptime(start_time.strip(), "%I:%M %p").time()
            parsed_end_time = datetime.strptime(end_time.strip(), "%I:%M %p").time()

            start_dt = datetime.combine(start_date, parsed_start_time)
            end_dt = datetime.combine(end_date, parsed_end_time)

            events.append(
                {
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                    "Event Title": title,
                    "Event Link": event_url,
                    "Organizer": config["organizer"],
                    "Industry": config["industry"],
                    "Market": config["market"],
                }
            )

        except Exception as e:
            print(f"[ERROR] Skipping event: {e}")
            continue

    return events


def process(config):
    print(f"[INFO] Processing: {config['url']}")
    event_list = get_event_list(config)
    if not event_list:
        print("No events found.")
        return []

    df = pd.DataFrame(event_list)
    print(df.to_string(index=False))
    return event_list
