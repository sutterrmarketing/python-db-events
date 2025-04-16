import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time
import pandas as pd
import re
from dateutil import parser

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}


def get_event_list(config):
    print(f"Fetching events from: {config['url']}")
    response = requests.get(config["url"], headers=headers, timeout=60)
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    for item in soup.select(config["event_list_selector"]):
        link_tag = item.select_one(config["event_link_selector"])
        title_tag = item.select_one(config["event_title_selector"])

        if not link_tag or not title_tag:
            continue

        event_url = urljoin(config["base_url"], link_tag.get("href"))
        event_title = title_tag.get_text(strip=True)

        raw_text = " ".join(item.stripped_strings)
        start_dt, start_time, end_dt, end_time = parse_range_text(raw_text)

        start_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
        end_date = end_dt.date() if isinstance(end_dt, datetime) else end_dt
        parsed_start_time = datetime.strptime(start_time.strip(), "%I:%M %p").time()
        parsed_end_time = datetime.strptime(end_time.strip(), "%I:%M %p").time()
        start_dt = datetime.combine(start_date, parsed_start_time)
        end_dt = datetime.combine(end_date, parsed_end_time)

        event_data = {
            "Weekday": start_dt.strftime("%A"),
            "start_dt": start_dt, 
            "end_dt": end_dt,
            "Event Title": event_title,
            "Event Link": event_url,
            "Organizer": config.get("organizer", "N/A"),
            "Industry": config.get("industry", "N/A"),
            "Market": config.get("market", "N/A"),
        }

        events.append(event_data)
    time.sleep(config.get("scraper_interval", 1))

    return events


def parse_range_text(raw_text):
    """
    Extracts start/end date and time from strings like:
    "From April 9, 2025, 5:30 pm to April 9, 2025, 7:30 pm"
    """
    pattern = r"From ([A-Za-z]+ \d{1,2}, \d{4}),\s*(\d{1,2}:\d{2}\s*[ap]m) to ([A-Za-z]+ \d{1,2}, \d{4})?,?\s*(\d{1,2}:\d{2}\s*[ap]m)"
    match = re.search(pattern, raw_text, re.IGNORECASE)

    if not match:
        print(f"[WARN] No match in: {raw_text}")
        return None, None, None, None

    start_date_str = match.group(1)
    start_time_str = match.group(2)
    end_date_str = match.group(3) or start_date_str  # fallback
    end_time_str = match.group(4)

    try:
        start_dt = datetime.strptime(start_date_str, "%B %d, %Y")
        end_dt = datetime.strptime(end_date_str, "%B %d, %Y")

        return start_dt, start_time_str, end_dt, end_time_str
    except Exception as e:
        print(f"[ERROR] Failed to parse datetime from: {raw_text} — {e}")
        return None, None, None, None


def process(config):
    print(f"Processing: {config['url']}")
    event_list = get_event_list(config)
    print(f"Found {len(event_list)} events")

    print(f"Collected {len(event_list)} valid events")
    if event_list:
        df = pd.DataFrame(event_list)
        print(df.to_string(index=False))

    return event_list
