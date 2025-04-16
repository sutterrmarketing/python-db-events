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
    """Fetch and parse event detail page for date and time."""
    ssl_verify = config.get("ssl_verify", True)
    response = requests.get(event_url, headers=headers, verify=ssl_verify, timeout=100)
    soup = BeautifulSoup(response.text, "html.parser")

    dt_config = config["detail_selectors"]["DateTime"]

    start_date_selector = dt_config.get("start_date_selector")
    end_date_selector = dt_config.get("end_date_selector")
    time_selector = dt_config.get("time_selector")

    # === Start Date ===
    start_dt = None
    start_date_elem = soup.select_one(start_date_selector)

    if start_date_elem:
        try:
            span_tags = start_date_elem.find_all("span")
            if span_tags:
                start_date_str = span_tags[-1].get_text(strip=True)
                start_dt = datetime.strptime(start_date_str, "%A, %B %d, %Y")
        except Exception as e:
            print(f"[ERROR] Failed to parse start date: {e}")
            return {}
    else:
        # === Try fallback date ===
        try:
            fallback_date_elem = soup.select_one(
                "div.o-details-block__details-info strong"
            )
            if fallback_date_elem:
                fallback_date_str = fallback_date_elem.get_text(strip=True)
                start_dt = datetime.strptime(fallback_date_str, "%A, %B %d, %Y")
                print(f"[INFO] Fallback date parsed at {event_url}")
            else:
                return {}
        except Exception as e:
            print(f"[ERROR] Fallback date parsing failed: {e}")
            return {}

    # === End Date ===
    end_dt = start_dt  # default
    end_date_elem = soup.select_one(end_date_selector)
    if end_date_elem:
        try:
            raw_end = end_date_elem.get_text(strip=True)
            if raw_end.lower().startswith("to "):
                raw_end = raw_end[3:]
            end_dt = datetime.strptime(raw_end, "%A, %B %d, %Y")
        except Exception as e:
            print(f"[WARN] Failed to parse end date, using start date instead: {e}")

    # === Time ===
    start_time, end_time = "12:00 AM", "11:59 PM"  # fallback defaults
    time_elem = soup.select_one(time_selector)

    if time_elem:
        try:
            time_str = time_elem.get_text(strip=True)
            time_range = time_str.split("(")[0].strip()
            if "-" in time_range:
                start_time, end_time = [t.strip() for t in time_range.split("-")]
        except Exception as e:
            print(f"[WARN] Failed to parse time '{time_str}', using default times: {e}")
    else:
        # === Fallback time block ===
        try:
            fallback_time_elem = soup.select_one(".o-details-block__details-copy")
            if fallback_time_elem:
                fallback_time_str = fallback_time_elem.get_text(strip=True).split(" (")[
                    0
                ]
                if "-" in fallback_time_str:
                    start_time, end_time = [
                        t.strip() for t in fallback_time_str.split("-")
                    ]
                    print(f"[INFO] Fallback time parsed at {event_url}")
        except Exception as e:
            print(f"[WARN] Fallback time parsing failed at {event_url}: {e}")

    start_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
    end_date = end_dt.date() if isinstance(end_dt, datetime) else end_dt

    parsed_start_time = datetime.strptime(start_time.strip(), "%I:%M %p").time()
    parsed_end_time = datetime.strptime(end_time.strip(), "%I:%M %p").time()

    start_dt = datetime.combine(start_date, parsed_start_time)
    end_dt = datetime.combine(end_date, parsed_end_time)

    time.sleep(config.get("scraper_interval", 1))
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
            "Market": config.get("market")
        }
        final_events.append(full_event)

    # list of events in the desired format:
    df = pd.DataFrame(final_events)
    print(df.to_string(index=False))

    return final_events
