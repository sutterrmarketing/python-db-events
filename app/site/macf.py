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
    time.sleep(config.get("scraper_interval", 1))  # polite delay

    return events


def get_event_details(event_url, config):
    """Parse start/end date and time from the event details page, handling variations in HTML structure."""

    base_delay = config.get("scraper_interval", 1)
    time.sleep(base_delay)

    response = requests.get(
        event_url, headers=headers, verify=config.get("ssl_verify", True), timeout=100
    )
    soup = BeautifulSoup(response.text, "html.parser")

    # Configuration for date and time extraction
    dt_config = config["detail_selectors"]["DateTime"]
    selector = dt_config["date_selector"]

    # Select the container that potentially contains the datetime text
    date_container = soup.select_one(selector)
    if not date_container:
        print(f"[WARN] Date information not found at {event_url}")
        return {}

    # Normalize and extract datetime text carefully
    dt_text = " ".join(
        date_container.stripped_strings
    )  # Efficiently collects all text, stripping excess whitespace

    # Remove "When:" prefix and normalize whitespace
    dt_text = dt_text.replace("When:", "").strip()
    dt_text = re.sub(r"\s+", " ", dt_text)  # Ensures no double spaces are present

    # print (dt_text)
    try:
        # print("[DEBUG] dt_text =", dt_text)

        if "Starts:" in dt_text and "Ends:" in dt_text:
            # Handle: Starts: May 15, 2025 09:00 AM (ET) Ends: May 18, 2025 05:00 PM (ET)
            match = re.search(
                r"Starts:\s*([A-Za-z]+ \d{1,2}, \d{4})\s+(\d{1,2}:\d{2} [APMapm]{2})"
                r".*?Ends:\s*([A-Za-z]+ \d{1,2}, \d{4})\s+(\d{1,2}:\d{2} [APMapm]{2})",
                dt_text,
            )
            if not match:
                raise ValueError("Failed to match 'Starts/Ends' format.")

            start_date_str, start_time_str, end_date_str, end_time_str = match.groups()
            # print(
            #     "[DEBUG] Special match:",
            #     start_date_str,
            #     start_time_str,
            #     end_date_str,
            #     end_time_str,
            # )

            start_dt = datetime.strptime(
                start_date_str + " " + start_time_str, "%B %d, %Y %I:%M %p"
            )
            end_dt = datetime.strptime(
                end_date_str + " " + end_time_str, "%B %d, %Y %I:%M %p"
            )

        else:
            # Handle: Apr 16, 2025 from 08:30 AM to 12:00 PM (ET)
            match = re.search(
                r"([A-Za-z]+ \d{1,2}, \d{4})\s+from\s+(\d{1,2}:\d{2} [APMapm]{2})\s+to\s+(\d{1,2}:\d{2} [APMapm]{2})",
                dt_text,
            )
            if not match:
                raise ValueError("Failed to match 'from/to' format.")

            date_str, start_time_str, end_time_str = match.groups()
            # print("[DEBUG] Standard match:", date_str, start_time_str, end_time_str)

            start_dt = datetime.strptime(
                date_str + " " + start_time_str, "%b %d, %Y %I:%M %p"
            )
            end_dt = datetime.strptime(date_str + " " + end_time_str, "%b %d, %Y %I:%M %p")

    except Exception as e:
        print(f"[ERROR] Failed to parse date/time at {event_url}: {e}")
        return {}

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
