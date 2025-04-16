import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time
import json, re
import pandas as pd

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}


def get_event_list(config):
    print(f"[INFO] Fetching from: {config['url']}")
    response = requests.get(config["url"], headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")
    script_tags = soup.select(config["event_data_selector"])

    events_json = None
    for tag in script_tags:
        try:
            data = json.loads(tag.string)
            if isinstance(data, list) and all("startDate" in e for e in data):
                events_json = data
                break
        except Exception:
            continue

    if not events_json:
        print("[ERROR] No valid event JSON-LD data found.")
        return []

    events = []
    for event in events_json:
        try:
            title = event.get("name")
            url = event.get("url")
            start = event.get("startDate")
            end = event.get("endDate")

            # Format datetimes
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)

            events.append(
                {
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                    "Event Title": title,
                    "Event Link": url,
                    "Organizer": config["organizer"],
                    "Industry": config["industry"],
                    "Market": config["market"],
                }
            )

        except Exception as e:
            print(f"[ERROR] Skipping event due to error: {e}")
            continue

    time.sleep(config.get("scraper_interval", 1))

    return events


def process(config):
    print(f"Processing: {config['url']}")
    event_list = get_event_list(config)
    if not event_list:
        print("No events found.")
        return []

    df = pd.DataFrame(event_list)
    print(df.to_string(index=False))
    return event_list
