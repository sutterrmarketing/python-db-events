import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time, re
import pandas as pd
import random

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}

def get_event_list(config):
    """Fetch the list of events from the website."""
    print(f"Fetching events from: {config['url']}")
    response = requests.get(config["url"], headers=headers, timeout=100)
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    for item in soup.select(config["event_list_selector"]):
        title_tag = item.select_one(config["event_title_selector"])
        link_tag = item.select_one(config["event_link_selector"])

        if not title_tag or not link_tag:
            continue

        title = title_tag.get_text(strip=True)
        if any(
            skipword.lower() in title.lower()
            for skipword in config.get("title_filter", [])
        ):
            print(f"[SKIP] Title filtered out: {title}")
            continue

        relative_url = link_tag.get("href")
        event_url = urljoin(config["base_url"], relative_url)

        events.append({"Event Title": title, "Event Link": event_url})

    if (config.get("scraper_interval", 1)) >= 10:
        print(f"[INFO] Please be patient, we have to reduce the speed to avoid a blocking from the website.")
    time.sleep(config.get("scraper_interval", 1))  # polite delay

    return events


def get_event_details(event_url, config):

    """Parse start/end date and time based on position of <p> tags."""

    base_delay = config.get("scraper_interval", 1)
    time.sleep(base_delay + random.uniform(1, 5))

    response = requests.get(event_url, headers=headers, timeout=100)
    soup = BeautifulSoup(response.text, "html.parser")

    dt_config = config["detail_selectors"]["DateTime"]
    selector = dt_config["date_selector"]["selector"]
    position = dt_config["date_selector"]["position"]

    p_tags = soup.select(selector)
    if len(p_tags) <= position:
        print(f"[WARN] Not enough <p> tags at {event_url}")
        return {}

    dt_text = p_tags[position].get_text(strip=True)

    # Clean & normalize
    dt_text = re.sub(r"Add to Calendar.*", "", dt_text).strip()
    dt_text = re.sub(r"(\d{4})(\d{1,2}:\d{2})", r"\1 \2", dt_text)

    # print(f"[DEBUG] Cleaned datetime: {dt_text}")

    try:
        parts = dt_text.split()
        date_str = " ".join(parts[:3])  # e.g., "March 26, 2025"
        time_str = dt_text.replace(date_str, "").strip()

        start_dt = datetime.strptime(date_str, "%B %d, %Y")
        start_time, end_time = "12:00 AM", "11:59 PM"
        if "-" in time_str:
            start_time, end_time = [t.strip() for t in time_str.split("-")]

    except Exception as e:
        print(f"[ERROR] Failed to parse date/time at {event_url}: {e}")
        return {}

    start_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
    end_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
    parsed_start_time = datetime.strptime(start_time.strip(), "%I:%M %p").time()
    parsed_end_time = datetime.strptime(end_time.strip(), "%I:%M %p").time()

    start_dt = datetime.combine(start_date, parsed_start_time)
    end_dt = datetime.combine(end_date, parsed_end_time)

    return {"start_dt": start_dt, "end_dt": end_dt}


def process(config):
    print(f"Processing: {config['url']}")
    event_list = get_event_list(config)
    print(f"Found {len(event_list)} events")

    final_events = []
    for event in event_list:
        details = get_event_details(event["Event Link"], config)
        if len(details) == 0:
            continue
        if not details:
            continue

        full_event = {
            **event,
            **details,
            "Organizer": config.get("organizer"),
            "Industry": config.get("industry"),
            "Market": config.get("market"),
        }

        final_events.append(full_event)

    print(f"Collected {len(final_events)} valid events")
    if final_events:
        df = pd.DataFrame(final_events)
        print(df.to_string(index=False))

    return final_events
