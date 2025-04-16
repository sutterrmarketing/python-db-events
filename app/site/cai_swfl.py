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
    response = requests.get(config["url"], headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    for item in soup.select(config["event_list_selector"]):
        link_tag = item.select_one(config["event_link_selector"])

        # Extract full title from `title` attribute of the surrounding span
        span_tag = item.select_one("span[title]")
        full_title = None
        if span_tag and span_tag.has_attr("title"):
            try:
                inner_html = span_tag["title"]
                inner_soup = BeautifulSoup(inner_html, "html.parser")
                title_div = inner_soup.select_one("div.jevtt_title")
                if title_div:
                    full_title = title_div.get_text(strip=True)
            except Exception as e:
                print(f"[WARN] Failed to extract title from span[title]: {e}")

        # Fallback to a-tag text if needed
        if not full_title and link_tag:
            full_title = link_tag.get_text(strip=True)

        if not link_tag or not full_title:
            continue

        event_url = urljoin(config["base_url"], link_tag.get("href"))

        events.append({"Event Title": full_title, "Event Link": event_url})

    time.sleep(config.get("scraper_interval", 1))

    return events


def parse_time_flexible(time_str):
    parts = time_str.strip().split()
    # Take only the first two parts (e.g., "10:00 AM") and ignore any timezone like EDT
    clean_time = " ".join(parts[:2])
    return datetime.strptime(clean_time, "%I:%M %p").time()


def get_event_details(event_url, config):
    time.sleep(config.get("scraper_interval", 1))
    response = requests.get(event_url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    dt_config = config["detail_selectors"]["DateTime"]

    # Date
    date_selector = dt_config.get("date_selector")
    date_elem = soup.select_one(date_selector)
    if not date_elem:
        print(f"[WARN] No date element found at {event_url}")
        return {}

    try:
        date_str = date_elem.get_text(strip=True)
        start_dt = datetime.strptime(date_str, "%A, %B %d, %Y")
    except Exception as e:
        print(f"[ERROR] Failed to parse date '{date_elem}': {e}")
        return {}

    # Time (from two separate selectors)
    time_selectors = dt_config.get("time_selector", [])
    if not isinstance(time_selectors, list) or len(time_selectors) != 2:
        print(f"[ERROR] Invalid time_selector format in config")
        return {}

    start_time_selector = time_selectors[0]["selector"]
    end_time_selector = time_selectors[1]["selector"]

    start_time_elem = soup.select_one(start_time_selector)
    end_time_elem = soup.select_one(end_time_selector)

    start_time = start_time_elem.get_text(strip=True) if start_time_elem else "12:00 AM"
    end_time = end_time_elem.get_text(strip=True) if end_time_elem else "11:59 PM"

    start_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
    end_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
    parsed_start_time = parse_time_flexible(start_time)
    parsed_end_time = parse_time_flexible(end_time)

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
