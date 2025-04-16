import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
from datetime import datetime
import time
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}

def parse_range_time(date_str, time_str):
    try:
        date_obj = datetime.strptime(date_str.strip(), "%B %d, %Y")
        times = re.findall(r"(\d{1,2}:\d{2}\s*[APMapm]{2})", time_str)

        if len(times) != 2:
            raise ValueError("Invalid time range")

        start_date = date_obj.date() if isinstance(date_obj, datetime) else date_obj
        end_date = date_obj.date() if isinstance(date_obj, datetime) else date_obj

        parsed_start_time = datetime.strptime(times[0].strip(), "%I:%M%p").time()
        parsed_end_time = datetime.strptime(times[1].strip(), "%I:%M%p").time()

        start_dt = datetime.combine(start_date, parsed_start_time)
        end_dt = datetime.combine(end_date, parsed_end_time)

        return {"start_dt": start_dt, "end_dt": end_dt}

    except Exception as e:
        print(f"[ERROR] Failed to parse date/time: {e}")
        return {}


def get_event_list(config):
    print(f"Fetching events from: {config['url']}")
    response = requests.get(config["url"], headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    for item in soup.select(config["event_list_selector"]):
        link_tag = item.select_one(config["event_link_selector"])
        date_tag = item.select_one(
            config["detail_selectors"]["DateTime"]["date_selector"]
        )
        time_tag = item.select_one(
            config["detail_selectors"]["DateTime"]["time_selector"]
        )

        if not link_tag or not date_tag or not time_tag:
            continue

        event_title = link_tag.get_text(strip=True)
        event_url = urljoin(config["base_url"], link_tag.get("href"))
        date_text = date_tag.get_text(strip=True)
        time_text = time_tag.get_text(strip=True)

        dt_info = parse_range_time(date_text, time_text)

        event_data = {
            "Event Title": event_title,
            "Event Link": event_url,
            **dt_info,
            "Organizer": config["organizer"],
            "Industry": config["industry"],
            "Market": config["market"],
        }

        events.append(event_data)
    time.sleep(config.get("scraper_interval", 1))

    print(f"Collected {len(events)} events")
    if events:
        df = pd.DataFrame(events)
        print(df.to_string(index=False))
        return events

    return []


def process(config):
    print(f"Processing: {config['url']}")
    event_list = get_event_list(config)

    def is_upcoming(event):
        try:
            start_date_str = event.get("Start Date")
            if not start_date_str:
                return False
            dt = datetime.strptime(start_date_str, "%Y-%m-%d")
            return dt >= datetime.now()
        except Exception as e:
            print(f"[WARN] Skipping event due to date parse error: {e}")
            return False

    # Case 1: DataFrame
    if isinstance(event_list, pd.DataFrame):
        if event_list.empty:
            print("No events found.")
            return []
        filtered_df = event_list[
            event_list["Start Date"].apply(
                lambda d: datetime.strptime(d, "%B %d, %Y") >= datetime.now()
            )
        ]
        if filtered_df.empty:
            print("No upcoming events found.")
            return []
        print(f"Filtered down to {len(filtered_df)} upcoming events.")
        print(filtered_df.to_string(index=False))
        return filtered_df

    # Case 2: List of dicts
    elif isinstance(event_list, list):
        if not event_list:
            print("No events found.")
            return []
        upcoming = [e for e in event_list if is_upcoming(e)]
        if not upcoming:
            print("No upcoming events found.")
            return []
        print(f"Filtered down to {len(upcoming)} upcoming events.")
        df = pd.DataFrame(upcoming)
        print(df.to_string(index=False))
        return upcoming

    else:
        print("[ERROR] Unsupported return type from get_event_list")
        return []
