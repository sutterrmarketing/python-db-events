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
    print(f"[INFO] Fetching from: {config['url']}")
    response = requests.get(config["url"], headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    event_blocks = soup.select(config["event_list_selector"])
    print(f"[INFO] Found {len(event_blocks)} event blocks")
    events = []

    for block in event_blocks:
        link_tag = block.select_one(config["event_link_selector"])
        title_tag = block.select_one(config["event_title_selector"])

        if not link_tag or not title_tag:
            continue

        event_url = urljoin(config["base_url"], link_tag.get("href"))
        event_title = title_tag.get_text(strip=True)

        event_data = {
            "Event Title": event_title,
            "Event Link": event_url,
            "Organizer": config["organizer"],
            "Industry": config["industry"],
            "Market": config["market"],
        }

        dt_info = get_event_details(event_url, config)
        if dt_info:
            event_data.update(dt_info)
            events.append(event_data)

    time.sleep(config.get("scraper_interval", 1) + random.uniform(1, 2))

    return events


def get_event_details(event_url, config):

    time.sleep(config.get("scraper_interval", 1) + random.uniform(1, 2))
    # print(f"[INFO] Fetching detail from: {event_url}")
    response = requests.get(event_url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    # Check for "SAMA Events" in the Community panel
    community_panel = soup.select_one("#MainCopy_ctl09_CommunityPanel")
    if not community_panel or "SAMA Events" not in community_panel.get_text():
        print(f"[INFO] Skipping event not associated with SAMA: {event_url}")
        return None

    dt_config = config["detail_selectors"]["DateTime"]
    elems = soup.select(dt_config["selector"])
    if not elems or len(elems) <= dt_config["position"]:
        print(f"[WARN] Cannot find datetime info on page: {event_url}")
        return {}

    raw_text = elems[dt_config["position"]].get_text(separator=" ", strip=True)
    # print(f"[DEBUG] Raw datetime text: {raw_text}")

    try:
        match = re.search(
            r"(\w{3} \d{1,2}, \d{4}) from ([\d: ]+[APMapm]{2}) to ([\d: ]+[APMapm]{2})",
            raw_text,
        )
        if not match:
            raise ValueError("Pattern not matched")

        date_str, start_time, end_time = match.groups()
        start_dt = datetime.strptime(date_str, "%b %d, %Y")

        start_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
        end_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
        parsed_start_time = datetime.strptime(start_time.strip(), "%I:%M %p").time()
        parsed_end_time = datetime.strptime(end_time.strip(), "%I:%M %p").time()

        start_dt = datetime.combine(start_date, parsed_start_time)
        end_dt = datetime.combine(end_date, parsed_end_time)

        return {"start_dt": start_dt, "end_dt": end_dt}


    except Exception as e:
        print(f"[ERROR] Failed to parse datetime at {event_url}: {e}")
        return {}


def process(config):
    print(f"[PROCESSING] {config['url']}")
    events = get_event_list(config)
    if not events:
        print("No events found.")
        return []

    df = pd.DataFrame(events)
    print(df.to_string(index=False))
    return events
