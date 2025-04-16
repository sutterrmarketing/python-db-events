import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time
import json, re
import pandas as pd
import pytz

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}


def extract_event_json(soup):
    """Finds the <script> tag containing 'const event =' and extracts the JSON data as a dictionary."""
    script_tags = soup.find_all("script")

    for script in script_tags:
        if "const event =" in script.text:  # Find the correct <script>
            match = re.search(r"const event = ({.*?});", script.text, re.DOTALL)
            if match:
                js_object = match.group(1)

                # Convert JavaScript object to Python dictionary manually
                event_data = {}

                # Extract key-value pairs using regex
                pairs = re.findall(
                    r"(\w+):\s*'([^']*)'|\b(\w+):\s*\"([^\"]*)\"", js_object
                )

                for pair in pairs:
                    key = pair[0] if pair[0] else pair[2]  # Get the correct key
                    value = pair[1] if pair[1] else pair[3]  # Get the correct value
                    event_data[key] = value.strip()  # Store in dictionary

                return event_data  # Return extracted event data as a Python dictionary

    return None


def get_event_list(config):
    print(f"Fetching events from: {config['url']}")
    response = requests.get(config["url"], headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    title_filter = config["title_filter"]

    events = []
    for item in soup.select(config["event_list_selector"]):
        link_tag = item.select_one(config["event_link_selector"])
        title_tag = item.select_one(config["event_title_selector"])

        if not link_tag or not title_tag:
            continue

        event_url = urljoin(config["base_url"], link_tag.get("href"))
        event_title = title_tag.get_text(strip=True)

        if any(word.lower() in event_title.lower() for word in title_filter):
            print(f"[SKIP] Filtered by title: {event_title}")
            continue

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
    event_data = extract_event_json(soup)
    if not event_data:
        print(f"[WARN] No JSON-LD Event found at {event_url}")
        return {}

    start_str = event_data.get("start")
    end_str = event_data.get("end")

    if not start_str or not end_str:
        print(f"[ERROR] Missing start or end date in JSON-LD at {event_url}")
        return {}

    eastern = pytz.timezone("America/New_York")

    try:
        start_dt = datetime.fromisoformat(start_str).astimezone(eastern)
        end_dt = datetime.fromisoformat(end_str).astimezone(eastern)
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
