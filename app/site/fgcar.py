import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import pandas as pd
import time

headers = {"User-Agent": "Mozilla/5.0"}


def get_event_list(config):
    print(f"Fetching: {config['url']}")
    response = requests.get(config["url"], headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    events = []

    title_filter = config.get("title_filter", [])

    for item in soup.select(config["event_list_selector"]):
        try:
            title_tag = item.select_one(config["event_title_selector"])
            start_meta = item.select_one(config["start_meta_selector"])
            end_meta = item.select_one(config["end_meta_selector"])

            if not (title_tag and start_meta and end_meta):
                continue

            title = title_tag.get_text(strip=True)
            url = urljoin(config["base_url"], title_tag.get("href"))

            if any(word.lower() in title.lower() for word in title_filter):
                print(f"[SKIP] Title filtered out: {title}")
                continue

            start_str = start_meta.get("content").strip()
            end_str = end_meta.get("content").strip()

            # Convert to datetime
            start_dt = datetime.strptime(start_str, "%m/%d/%Y %I:%M:%S %p")
            end_dt = datetime.strptime(end_str, "%m/%d/%Y %I:%M:%S %p")

            event = {
                "start_dt": start_dt,
                "end_dt": end_dt,
                "Event Title": title,
                "Event Link": url,
                "Organizer": config["organizer"],
                "Industry": config["industry"],
                "Market": config["market"],
            }

            events.append(event)
            time.sleep(config.get("scraper_interval", 1))

        except Exception as e:
            print(f"[ERROR] Skipping event: {e}")
            continue

    return events


def process(config):
    event_list = get_event_list(config)
    print(f"Collected {len(event_list)} events")
    if event_list:
        df = pd.DataFrame(event_list)
        print(df.to_string(index=False))
        return event_list
    return []
