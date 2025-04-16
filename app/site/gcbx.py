import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
import pandas as pd
import re
import time
import pytz

headers = {"User-Agent": "Mozilla/5.0"}


def extract_event_script_data(soup):
    """Extract start/end datetime from embedded <script> block."""
    script_tags = soup.find_all("script")
    for script in script_tags:
        if script.string and "const event = {" in script.string:
            match = re.search(
                r"const event\s*=\s*(\{.*?\})\s*;", script.string, re.DOTALL
            )
            if not match:
                continue

            event_js = match.group(1)
            # Extract start and end datetime using regex
            start = re.search(r"start\s*:\s*'([^']+)'", event_js)
            end = re.search(r"end\s*:\s*'([^']+)'", event_js)

            return {
                "start": start.group(1) if start else None,
                "end": end.group(1) if end else None,
            }
    return {}


def get_event_list(config):
    print(f"Fetching events from: {config['url']}")
    response = requests.get(config["url"], headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    for item in soup.select(config["event_list_selector"]):
        title_tag = item.select_one(config["event_title_selector"])
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        event_url = urljoin(config["base_url"], title_tag.get("href"))

        events.append({"Event Title": title, "Event Link": event_url})

    time.sleep(config.get("scraper_interval", 1))

    return events


def get_event_details(event_url):
    response = requests.get(event_url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    event_data = extract_event_script_data(soup)
    if not event_data.get("start") or not event_data.get("end"):
        print(f"[WARN] No start/end datetime for: {event_url}")
        return {}

    try:
        # Parse ISO 8601 UTC datetimes
        start_dt_utc = datetime.fromisoformat(
            event_data["start"].replace("Z", "+00:00")
        )
        end_dt_utc = datetime.fromisoformat(event_data["end"].replace("Z", "+00:00"))

        # Convert directly to America/New_York
        eastern = pytz.timezone("America/New_York")
        start_dt = start_dt_utc.astimezone(eastern)
        end_dt = end_dt_utc.astimezone(eastern)

    except Exception as e:
        print(f"[ERROR] Failed to parse/convert datetimes: {e}")
        return {}

    return {"start_dt": start_dt, "end_dt": end_dt}


def process(config):
    event_list = get_event_list(config)
    print(f"Found {len(event_list)} events")

    final_events = []
    for event in event_list:
        details = get_event_details(event["Event Link"])
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
    return []
