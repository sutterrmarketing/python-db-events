import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time
import json
import pandas as pd

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}


def extract_json_ld(soup):
    """Extract JSON-LD data from a script tag."""
    json_ld_tags = soup.find_all("script", {"type": "application/ld+json"})

    if not json_ld_tags:
        return None

    for json_ld_tag in json_ld_tags:
        try:
            json_ld_data = json.loads(json_ld_tag.string)  # Parse JSON

            # Case 1: Directly contains an Event
            if "@type" in json_ld_data and json_ld_data["@type"] == "Event":
                return json_ld_data  # Return the valid event

            # Case 2: JSON is a list of objects, find the first "Event"
            if isinstance(json_ld_data, list):
                for obj in json_ld_data:
                    if "@type" in obj and obj["@type"] == "Event":
                        return obj  # Return the valid event
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON-LD: {e}")
    return None


def get_event_list(config):
    print(f"Fetching events from: {config['url']}")
    response = requests.get(config["url"], headers=headers, timeout=30)
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

    time.sleep(config.get("scraper_interval", 1))

    return events


def get_event_details(event_url, config):

    time.sleep(config.get("scraper_interval", 1))

    response = requests.get(event_url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    # === Category Filtering ===
    category_selector = config["detail_selectors"].get("Event Category")
    category_filter = config["detail_selectors"].get("Event Category Filter", [])

    if category_selector:
        category_tags = soup.select(category_selector)
        category_slugs = [
            tag.get("href", "").strip("/").split("/")[-1].lower()
            for tag in category_tags
        ]
        if any(slug in category_filter for slug in category_slugs):
            print(f"[SKIP] Category filtered out: {category_slugs}")
            return {}

    # === JSON-LD Parsing using extract_json_ld helper ===
    event_data = extract_json_ld(soup)
    if not event_data:
        print(f"[WARN] No JSON-LD Event found at {event_url}")
        return {}

    start_str = event_data.get("startDate")
    end_str = event_data.get("endDate")

    if not start_str or not end_str:
        print(f"[ERROR] Missing start or end date in JSON-LD at {event_url}")
        return {}

    try:
        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)
    except Exception as e:
        print(f"[ERROR] Failed to parse ISO datetimes: {e}")
        return {}

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

    print(f"Filtered down to {len(final_events)} valid events")
    if final_events:
        df = pd.DataFrame(final_events)
        print(df.to_string(index=False))

    return final_events
