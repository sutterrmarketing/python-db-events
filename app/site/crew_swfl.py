import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import time
import json

headers = {"User-Agent": "Mozilla/5.0"}


def extract_events_from_jsonld(soup):
    """Extract list of JSON-LD event objects from <script type='application/ld+json'>."""
    scripts = soup.find_all("script", {"type": "application/ld+json"})
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list) and all(d.get("@type") == "Event" for d in data):
                return data
        except Exception as e:
            print(f"[WARN] Failed to parse JSON-LD: {e}")
    return []


def get_event_list(config):
    print(f"Fetching: {config['url']}")
    response = requests.get(config["url"], headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    json_events = extract_events_from_jsonld(soup)
    event_list = []

    title_filter = config.get("title_filter", [])

    for item in json_events:
        try:
            title = item.get("name", "").strip()
            link = item.get("url", "").strip()

            if any(kw.lower() in title.lower() for kw in title_filter):
                print(f"[SKIP] Filtered by title: {title}")
                continue

            start_str = item.get("startDate")
            end_str = item.get("endDate")

            if not start_str or not end_str:
                continue

            start_dt = datetime.fromisoformat(start_str)
            end_dt = datetime.fromisoformat(end_str)

            event = {
                "Event Title": title,
                "Event Link": link,
                "start_dt": start_dt,
                "end_dt": end_dt,
                "Organizer": config["organizer"],
                "Industry": config["industry"],
                "Market": config["market"],
            }

            event_list.append(event)
            time.sleep(config.get("scraper_interval", 1))

        except Exception as e:
            print(f"[ERROR] Skipping event due to error: {e}")
            continue

    return event_list


def process(config):
    event_list = get_event_list(config)
    print(f"Collected {len(event_list)} events")
    if event_list:
        df = pd.DataFrame(event_list)
        print(df.to_string(index=False))
        return event_list
    return []
