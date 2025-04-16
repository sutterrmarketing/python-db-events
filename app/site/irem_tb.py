import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import pandas as pd
import time
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}
def parse_datetime_range(text):
    """
    Parses text like 'April 16, 2025 9:00 AM - 12:00 PM' into structured datetime.
    """
    try:
        match = re.match(
            r"([A-Za-z]+\s+\d{1,2},\s+\d{4})\s+(\d{1,2}:\d{2}\s*[APMapm]{2})\s*-\s*(\d{1,2}:\d{2}\s*[APMapm]{2})",
            text.strip(),
        )
        if not match:
            return None

        date_str = match.group(1)
        start_time_str = match.group(2)
        end_time_str = match.group(3)

        start_dt = datetime.strptime(
            f"{date_str} {start_time_str}", "%B %d, %Y %I:%M %p"
        )
        end_dt = datetime.strptime(f"{date_str} {end_time_str}", "%B %d, %Y %I:%M %p")

        return {"start_dt": start_dt, "end_dt": end_dt}

    except Exception as e:
        print(f"[ERROR] Failed to parse datetime string '{text}': {e}")
        return {}


def get_event_details(url, dt_config):
    try:
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        date_selector = dt_config["datetime_selector"]["selector"]
        date_position = dt_config["datetime_selector"].get("position", 0)

        date_elems = soup.select(date_selector)
        if not date_elems or len(date_elems) <= date_position:
            return {}

        raw_datetime = date_elems[date_position].get_text(strip=True)
        # Fix missing space between date and time (e.g. "20259:00" -> "2025 9:00")
        raw_datetime = re.sub(r"(\d{4})(\d{1,2}:\d{2})", r"\1 \2", raw_datetime)

        # Remove trailing words like "Add to Calendar"
        raw_datetime = re.sub(r"Add to Calendar.*", "", raw_datetime, flags=re.IGNORECASE).strip()

        return parse_datetime_range(raw_datetime)

    except Exception as e:
        print(f"[ERROR] Failed to fetch details for {url}: {e}")
        return {}


def get_event_list(config):
    print(f"Fetching events from: {config['url']}")
    response = requests.get(config["url"], headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")
    title_filter = config["title_filter"]
    events = []
    for item in soup.select(config["event_list_selector"]):
        link_tag = item.select_one(config["event_link_selector"])
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)
        url = urljoin(config["base_url"], link_tag.get("href"))

        if any(word.lower() in title.lower() for word in title_filter):
            print(f"[SKIP] Title filtered out: {title}")
            continue

        events.append({"Event Title": title, "Event Link": url})

    time.sleep(config.get("scraper_interval", 1))

    return events


def process(config):
    event_list = get_event_list(config)
    print(f"Found {len(event_list)} events")

    final_events = []
    for event in event_list:
        details = get_event_details(
            event["Event Link"], config["detail_selectors"]["DateTime"]
        )
        if not details:
            continue

        full_event = {
            **event,
            **details,
            "Organizer": config["organizer"],
            "Industry": config["industry"],
            "Market": config["market"],
        }

        final_events.append(full_event)

    print(f"Collected {len(final_events)} valid events")
    if final_events:
        df = pd.DataFrame(final_events)
        print(df.to_string(index=False))
        return final_events
    return []
