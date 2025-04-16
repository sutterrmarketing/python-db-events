import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time
import pandas as pd
import re
import pytz

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}


def extract_event_json(soup):
    """Finds the <script> tag containing 'const event =' and extracts the JSON data as a dictionary."""
    script_tags = soup.find_all("script")

    for script in script_tags:
        if "const event =" in script.text:
            match = re.search(r"const event\s*=\s*({.*?});", script.text, re.DOTALL)
            if match:
                js_object = match.group(1)

                event_data = {}

                # Match both single- and double-quoted values
                pairs = re.findall(
                    r"(\w+):\s*'([^']*)'|\b(\w+):\s*\"([^\"]*)\"", js_object
                )

                for pair in pairs:
                    key = pair[0] if pair[0] else pair[2]
                    value = pair[1] if pair[1] else pair[3]
                    event_data[key] = value.strip()

                return event_data

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

        event = {
            "Event Title": title_tag.get_text(strip=True),
            "Event Link": event_url,
        }

        events.append(event)
    time.sleep(config.get("scraper_interval", 1))  # polite delay

    return events


def get_event_details(event_url, config):

    time.sleep(config.get("scraper_interval", 1))  # polite delay

    """Extract event details using script:event.,key-based selectors and apply address filtering."""
    ssl_verify = config.get("ssl_verify", True)
    response = requests.get(event_url, headers=headers, verify=ssl_verify, timeout=100)
    soup = BeautifulSoup(response.text, "html.parser")

    event_data = extract_event_json(soup)

    if not event_data:
        return {}

    # Address filtering
    address = event_data.get("location", "").strip()
    address_filter = config["detail_selectors"].get("Address_filter", [])
    if any(address.lower().startswith(f.lower()) for f in address_filter):
        print(f"[SKIP] Address filtered out: {address}")
        return {}

    try:
        start_dt_utc = datetime.fromisoformat(event_data["start"].replace("Z", "+00:00"))
        end_dt_utc = datetime.fromisoformat(event_data["end"].replace("Z", "+00:00"))
    except Exception as e:
        print(f"[ERROR] Failed to parse datetime: {e}")
        return {}

    eastern = pytz.timezone("America/New_York")
    start_dt = start_dt_utc.astimezone(eastern)
    end_dt = end_dt_utc.astimezone(eastern)

    return {
        "start_dt": start_dt,
        "end_dt": end_dt,
        "Address": address,
        "Event name": event_data.get("title", "").strip(),
        "Event Link": event_url,
    }

def process(config):
    print(f"Processing: {config['url']}")

    event_list = get_event_list(config)
    print(f"Found {len(event_list)} events in list")

    final_events = []

    for event in event_list:
        details = get_event_details(event["Event Link"], config)

        if not details:
            continue  # Filtered or failed

        full_event = {
            **event,
            **details,
            "Organizer": config.get("organizer"),
            "Industry": config.get("industry"),
            "Market": config.get("market"),
        }

        final_events.append(full_event)

    print(f"Filtered down to {len(final_events)} final events")
    if final_events:
        df = pd.DataFrame(final_events)
        print(df.to_string(index=False))

    return final_events
