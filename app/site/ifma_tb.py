import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import pandas as pd
import time
import re
import pytz

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}

def extract_event_script_json(soup):
    """Extract values from 'const event = { ... }' script block."""
    script_tags = soup.find_all("script")
    for script in script_tags:
        if script.string and "const event =" in script.string:
            match = re.search(r"const event\s*=\s*(\{.*?\});", script.string, re.DOTALL)
            if not match:
                continue

            block = match.group(1)

            def extract_field(key):
                m = re.search(rf"{key}\s*:\s*['\"](.*?)['\"]", block)
                return m.group(1).strip() if m else None

            return {
                "start": extract_field("start"),
                "end": extract_field("end"),
            }
    return {}


def get_event_list(config):
    print(f"Fetching: {config['url']}")
    response = requests.get(
        config["url"],
        headers=headers,
        verify=config.get("ssl_verify", True),
        timeout=30,
    )
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    for item in soup.select(config["event_list_selector"]):
        link_tag = item.select_one(config["event_link_selector"])
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)
        url = urljoin(config["base_url"], link_tag.get("href"))

        events.append({"Event Title": title, "Event Link": url})

    time.sleep(config.get("scraper_interval", 1))

    return events


def get_event_details(event_url):
    response = requests.get(event_url, headers=headers, timeout=30, verify=False)
    soup = BeautifulSoup(response.text, "html.parser")
    data = extract_event_script_json(soup)

    if not data.get("start") or not data.get("end"):
        return {}

    eastern = pytz.timezone("America/New_York")

    try:
        start_dt = datetime.fromisoformat(data["start"].replace("Z", "+00:00")).astimezone(eastern)
        end_dt = datetime.fromisoformat(data["end"].replace("Z", "+00:00")).astimezone(eastern)
    except Exception as e:
        print(f"[ERROR] Failed to parse datetimes: {e}")
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
