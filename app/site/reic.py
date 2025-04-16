import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time
import json, re, random
import pandas as pd

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}


def get_event_list(config):
    response = requests.get(config["url"], headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")
    events = []

    for row in soup.select(config["event_list_selector"]):
        link_tag = row.select_one(config["event_link_selector"])
        title_tag = row.select_one(config["event_title_selector"])

        if not link_tag or not title_tag:
            continue

        event_url = urljoin(config["base_url"], link_tag.get("href"))
        event_title = title_tag.get_text(strip=True)

        event = {"Event Title": event_title, "Event Link": event_url}

        events.append(event)
    time.sleep(config.get("scraper_interval", 1) + random.uniform(0.3, 1.2))

    return events


def get_event_details(event_url, config):
    """Fetch and parse event details including start and end date/time."""
    try:
        time.sleep(config.get("scraper_interval", 1) + random.uniform(1, 4))

        response = requests.get(event_url, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        dt_config = config["detail_selectors"]["DateTime"]
        start_date_selector = dt_config.get("start_date_selector", ".event-start-date")
        start_time_selector = dt_config.get("start_time_selector", ".event-start-time")
        end_time_selector = dt_config.get("end_time_selector", ".event-stop-time")

        start_date_elem = soup.select_one(start_date_selector)
        start_time_elem = soup.select_one(start_time_selector)
        end_time_elem = soup.select_one(end_time_selector)

        if not (start_date_elem and start_time_elem and end_time_elem):
            print(f"[WARN] Missing date/time elements on page: {event_url}")
            return {}

        raw_date = start_date_elem.get_text(strip=True)
        raw_start_time = start_time_elem.get_text(strip=True)
        raw_end_time = end_time_elem.get_text(strip=True)

        # Clean up trailing timezone like "EDT"
        raw_end_time = re.sub(r"\s*[A-Z]{2,4}$", "", raw_end_time.strip())

        # Extract actual date string
        date_match = re.search(r"[A-Za-z]+day, ([A-Za-z]+ \d{1,2}, \d{4})", raw_date)
        if not date_match:
            print(f"[ERROR] Failed to extract full date: {raw_date}")
            return {}

        date_str = date_match.group(1)
        start_dt = datetime.strptime(date_str, "%B %d, %Y")

        # Fix end time if AM/PM is missing
        if not re.search(r"(am|pm)", raw_end_time, re.IGNORECASE):
            meridiem = "AM" if "am" in raw_start_time.lower() else "PM"
            raw_end_time = f"{raw_end_time.strip()} {meridiem}"

        start_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
        end_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
        parsed_start_time = datetime.strptime(raw_start_time.strip(), "%I:%M %p").time()
        parsed_end_time = datetime.strptime(raw_end_time.strip(), "%I:%M %p").time()

        start_dt = datetime.combine(start_date, parsed_start_time)
        end_dt = datetime.combine(end_date, parsed_end_time)

        return {"start_dt": start_dt, "end_dt": end_dt}

    except Exception as e:
        print(f"[ERROR] Failed to parse date/time at {event_url}: {e}")
        return {}


def process(config):
    print(f"Processing: {config['url']}")
    event_list = get_event_list(config)
    if not event_list:
        print("No events found.")
        return []

    final_events = []
    for event in event_list:
        details = get_event_details(event["Event Link"], config)
        if not details:
            continue

        event_data = {
            **event,
            **details,
            "Organizer": config["organizer"],
            "Industry": config["industry"],
            "Market": config["market"],
        }
        final_events.append(event_data)

    if not final_events:
        print("No valid events.")
        return []

    df = pd.DataFrame(final_events)
    print(df.to_string(index=False))
    return final_events
