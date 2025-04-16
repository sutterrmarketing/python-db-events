import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time
import pandas as pd

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}

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

        event = {"Event Title": title_tag.get_text(strip=True), "Event Link": event_url}

        events.append(event)
        
    return events


def get_event_details(event_url, config):
    """Extract start and end datetime from separate spans, with fallback if one is missing."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(event_url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, "html.parser")

    dt_config = config["detail_selectors"]["DateTime"]
    start_sel = dt_config.get("start_date_selector")
    end_sel = dt_config.get("end_date_selector")

    def parse_datetime(selector, label):
        if not selector:
            return None
        elem = soup.select_one(selector)
        if not elem:
            print(f"[WARN] Missing {label} selector: {selector}")
            return None
        text = elem.get_text(separator=" ", strip=True).replace("\xa0", " ")
        if "@" not in text:
            print(f"[WARN] Missing '@' in {label} text: '{text}'")
            return None
        try:
            date_part, time_part = [s.strip() for s in text.split("@")]
            return datetime.strptime(f"{date_part} {time_part}", "%m-%d-%Y %I:%M %p")
        except Exception as e:
            print(f"[ERROR] Failed to parse {label}: '{text}' => {e}")
            return None

    start_dt = parse_datetime(start_sel, "start datetime")
    end_dt = parse_datetime(end_sel, "end datetime")

    # Fallback: use the one that exists for both
    if not start_dt and end_dt:
        start_dt = end_dt
    if not end_dt and start_dt:
        end_dt = start_dt

    if not start_dt:
        print(f"[ERROR] Could not parse any datetime from {event_url}")
        return {}

    time.sleep(config.get("scraper_interval", 1))  # polite delay

    return {"start_dt": start_dt, "end_dt": end_dt}

def process(config):
    print(f"Processing: {config['url']}")
    event_list = get_event_list(config)
    print(f"Found {len(event_list)} events")

    final_events = []

    for event in event_list:
        detail = get_event_details(event["Event Link"], config)
        if len(detail) == 0:
            continue
        full_event = {
            **event,
            **detail,
            "Organizer": config.get("organizer"),
            "Industry": config.get("industry"),
            "Market": config.get("market"),
        }
        final_events.append(full_event)

    # list of events in the desired format:
    df = pd.DataFrame(final_events)
    print(df.to_string(index=False))

    return final_events
