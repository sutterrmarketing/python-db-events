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
    print(f"Fetching: {config['url']}")
    response = requests.get(config["url"], headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    for block in soup.select(config["event_list_selector"]):
        try:
            title_tag = block.select_one(config["event_title_selector"])
            link_tag = block.select_one(config["event_link_selector"])
            time_text = " ".join(
                t.get_text(strip=True)
                for t in block.select(config["event_time_selector"])
            )
            date_stub = block.select_one(config["date_attr_selector"])

            if not (title_tag and link_tag and date_stub):
                continue

            title = title_tag.get_text(strip=True)
            relative_url = link_tag.get("href", "")
            event_url = urljoin(config["base_url"], relative_url)

            # Extract date and time from title attribute
            title_attr = date_stub.get("title", "")
            match = re.search(r"Starts (.+?) at (.+)", title_attr)
            if match:
                date_str = match.group(1)
                time_str = match.group(2)
                start_dt = datetime.strptime(
                    f"{date_str} {time_str}", "%B %d, %Y %I:%M %p"
                )
            else:
                continue

            # Extract time range if available (e.g., "9:30 AM - 3:00 PM")
            start_time = start_dt.strftime("%I:%M %p")
            end_time = None
            time_range_match = re.search(
                r"(\d{1,2}:\d{2}\s*[APMapm]{2})\s*-\s*(\d{1,2}:\d{2}\s*[APMapm]{2})",
                time_text,
            )
            if time_range_match:
                start_time = time_range_match.group(1)
                end_time = time_range_match.group(2)

            start_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
            end_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
            parsed_start_time = datetime.strptime(start_time.strip(), "%I:%M %p").time()
            parsed_end_time = datetime.strptime(end_time.strip(), "%I:%M %p").time()

            start_dt = datetime.combine(start_date, parsed_start_time)
            end_dt = datetime.combine(end_date, parsed_end_time)

            event_data = {
                "start_dt": start_dt,
                "end_dt": end_dt,
                "Event Title": title,
                "Event Link": event_url,
                "Organizer": config.get("organizer"),
                "Industry": config.get("industry"),
                "Market": config.get("market"),
            }

            events.append(event_data)
            time.sleep(config.get("scraper_interval", 1))

        except Exception as e:
            print(f"[ERROR] Failed to parse block: {e}")
            continue

    return events


def process(config):
    event_list = get_event_list(config)
    print(f"Collected {len(event_list)} events")

    if event_list:
        df = pd.DataFrame(event_list)
        print(df.to_string(index=False))
        return df

    return []
