import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time, re
import pandas as pd

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
        title_tag = item.select_one(config["event_title_selector"])
        time_tag = item.select_one(config["event_time_selector"])

        if not title_tag or not time_tag:
            continue

        event_name = title_tag.get("title", "").strip()
        event_url = urljoin(config["base_url"], title_tag.get("href"))

        time_text = time_tag.get_text(strip=True)
        # Example format: "Apr 9, 05:00 PM - 08:00 PM (ET)"
        match = re.match(
            r"([A-Za-z]+ \d{1,2}),\s*(\d{1,2}:\d{2}\s*[APMapm]{2})\s*-\s*(\d{1,2}:\d{2}\s*[APMapm]{2})",
            time_text,
        )
        if not match:
            print(f"[WARN] Failed to parse time string: {time_text}")
            continue

        try:
            year = datetime.now().year  # or pull from elsewhere if it's not current
            date_str = f"{match.group(1)} {year}"  # e.g. "Apr 9 2025"
            start_dt = datetime.strptime(date_str, "%b %d %Y")

            start_time = match.group(2)
            end_time = match.group(3)

            start_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
            end_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt

            parsed_start_time = datetime.strptime(start_time.strip(), "%I:%M %p").time()
            parsed_end_time = datetime.strptime(end_time.strip(), "%I:%M %p").time()

            start_dt = datetime.combine(start_date, parsed_start_time)
            end_dt = datetime.combine(end_date, parsed_end_time)

            event_data = {
                "start_dt": start_dt,
                "end_dt": end_dt,
                "Event Title": event_name,
                "Event Link": event_url,
                "Organizer": config["organizer"],
                "Industry": config["industry"],
                "Market": config["market"],
            }

            events.append(event_data)
        except Exception as e:
            print(f"[ERROR] Failed to parse date/time: {e}")

    time.sleep(config.get("scraper_interval", 1))

    return events


def process(config):
    event_list = get_event_list(config)
    print(f"Collected {len(event_list)} events")

    if event_list:
        df = pd.DataFrame(event_list)
        print(df.to_string(index=False))
        return event_list

    return []
