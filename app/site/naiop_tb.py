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


def extract_start_end_from_embedded_js(soup):
    """
    Extracts 'start' and 'end' ISO8601 datetime strings from <script> blocks
    that define JS 'event' objects (like on WildApricot-powered sites).

    Returns (start_str, end_str) or (None, None) if not found.
    """
    script_tags = soup.find_all("script")

    for script in script_tags:
        script_text = script.string or script.text
        if not script_text:
            continue

        # Look for JS object definition containing "const event = {"
        if (
            "const event" in script_text
            and "start" in script_text
            and "end" in script_text
        ):
            try:
                start_match = re.search(r"start\s*:\s*['\"](.*?)['\"]", script_text)
                end_match = re.search(r"end\s*:\s*['\"](.*?)['\"]", script_text)

                start = start_match.group(1) if start_match else None
                end = end_match.group(1) if end_match else None

                if start and end:
                    return start, end
            except Exception as e:
                print(f"[ERROR] Failed to extract start/end from JS event: {e}")
                continue

    return None, None


def get_event_details(url, config):
    response = requests.get(url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    dt_config = config["detail_selectors"]["DateTime"]

    eastern = pytz.timezone("America/New_York")

    if dt_config["start_dt_selector"].startswith("script:event."):
        start_str, end_str = extract_start_end_from_embedded_js(soup)

        try:
            start_dt = datetime.fromisoformat(
                start_str.replace("Z", "+00:00")
            ).astimezone(eastern)
            end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00")).astimezone(
                eastern
            )

            return {"start_dt": start_dt, "end_dt": end_dt}

        except Exception as e:
            print(f"[ERROR] Failed to parse ISO datetimes: {e}")
            return None

    return None


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
