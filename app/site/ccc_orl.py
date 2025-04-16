import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time
import pandas as pd

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

        events.append({"Event Title": event_title, "Event Link": event_url})

    if (config.get("scraper_interval", 1)) >= 10:
        print(
            f"[INFO] Please be patient, we have to reduce the speed to avoid a blocking from the website."
        )
    time.sleep(config.get("scraper_interval", 1))

    return events


def get_event_details(event_url, config):

    time.sleep(config.get("scraper_interval", 1))
    response = requests.get(event_url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    dt_config = config["detail_selectors"]["DateTime"]

    date_elem = soup.select_one(dt_config["date_selector"])
    time_elem = soup.select_one(dt_config["time_selector"])

    if not date_elem or not time_elem:
        print(f"[WARN] Missing date or time at {event_url}")
        return {}

    try:
        date_str = date_elem.get_text(strip=True)
        start_dt = datetime.strptime(date_str, "%B %d, %Y")
    except Exception as e:
        print(f"[ERROR] Failed to parse date '{date_str}': {e}")
        return {}

    start_time = "12:00 AM"
    end_time = "11:59 PM"

    try:
        time_str = time_elem.get_text(strip=True)
        if "-" in time_str:
            parts = [t.strip() for t in time_str.split("-")]
            if len(parts) == 2:
                start_time, end_time = parts
    except Exception as e:
        print(f"[WARN] Failed to parse time range: {e}")

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
