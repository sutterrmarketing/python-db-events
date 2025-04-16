import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time
import pandas as pd
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}


def parse_weekday_date_time_tz(text):
    """
    Example input: "Tuesday, April 1, 2025 (9:00 AM - 10:30 AM) (EDT)"
    """
    try:
        # Remove timezone part if present (e.g., "(EDT)")
        cleaned = re.sub(r"\s*\(GMT[^\)]*\)", "", text)
        cleaned = re.sub(r"\s*\([A-Z]+\)", "", cleaned)

        # Extract parts
        match = re.match(
            r"([A-Za-z]+,\s+[A-Za-z]+\s+\d{1,2},\s+\d{4})\s*\(([^)]+)\)", cleaned
        )
        if not match:
            print(f"[WARN] Unexpected format: {text}")
            return None, None, None, None, None

        date_part = match.group(1)
        time_range = match.group(2)

        start_dt = datetime.strptime(date_part.strip(), "%A, %B %d, %Y")

        if " - " in time_range:
            start_time, end_time = [t.strip() for t in time_range.split(" - ")]
        else:
            start_time = end_time = "12:00 AM"

        start_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
        end_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt

        parsed_start_time = datetime.strptime(start_time.strip(), "%I:%M %p").time()
        parsed_end_time = datetime.strptime(end_time.strip(), "%I:%M %p").time()

        start_dt = datetime.combine(start_date, parsed_start_time)
        end_dt = datetime.combine(end_date, parsed_end_time)

        return {"start_dt": start_dt, "end_dt": end_dt}

    except Exception as e:
        print(f"[ERROR] Failed to parse date/time string: {text} | {e}")
        return None


def get_event_list(config):
    """Fetch the list of events from the website."""
    print(f"Fetching events from: {config['url']}")
    ssl_verify = config.get("ssl_verify", True)
    response = requests.get(
        config["url"], headers=headers, verify=ssl_verify, timeout=100
    )

    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    list_selector = config["event_list_selector"]
    link_selector = config["event_link_selector"]
    title_selector = config["event_title_selector"]

    for item in soup.select(list_selector):
        link_tag = item.select_one(link_selector)
        title_tag = item.select_one(title_selector)

        if not link_tag or not title_tag:
            continue

        relative_url = link_tag.get("href")
        event_url = urljoin(config["base_url"], relative_url)

        event = {"Event Title": title_tag.get_text(strip=True), "Event Link": event_url}

        events.append(event)

    if (config.get("scraper_interval", 1)) >= 10:
        print(
            f"[INFO] Please be patient, we have to reduce the speed to avoid a blocking from the website."
        )
    time.sleep(config.get("scraper_interval", 1))  # polite delay

    print (len(events), "total events found.")
    title_filter = config.get("title_filter", [])

    filtered_events = []
    for event in events:
        title = event["Event Title"]
        if any(phrase.lower() in title.lower() for phrase in title_filter):
            print(f"[SKIP] Filtered by title: {title}")
            continue
        filtered_events.append(event)

    print(len(filtered_events), " events left.")
    return filtered_events


def get_event_details(event_url, config):

    time.sleep(config.get("scraper_interval", 1))  # polite delay

    """Fetch and parse event detail page for date and time."""
    ssl_verify = config.get("ssl_verify", True)
    response = requests.get(
        event_url, headers=headers, verify=ssl_verify, timeout=100
    )
    soup = BeautifulSoup(response.text, "html.parser")

    dt_config = config["detail_selectors"]["DateTime"]

    dt_selector = dt_config.get("date_selector")

    span = soup.select_one(dt_selector)
    if not span:
        print(f"[WARN] No date/time span found at {event_url}")
        return {}

    full_text = span.get_text(" ", strip=True)  # merge inner text with spaces
    return parse_weekday_date_time_tz(full_text) or {}


def process(config):
    print(f"Processing: {config['url']}")
    event_list = get_event_list(config)
    print(f"Found {len(event_list)} events")

    final_events = []

    for event in event_list:
        detail = get_event_details(event["Event Link"], config)
        if len(detail) == 0:
            continue
        full_event = {
            **event,
            **detail,
            "Organizer": config.get("organizer"),
            "Industry": config.get("industry"),
            "Market": config.get("market"),
        }
        final_events.append(full_event)

    # list of events in the desired format:
    df = pd.DataFrame(final_events)
    print(df.to_string(index=False))

    return final_events
