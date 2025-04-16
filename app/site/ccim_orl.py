import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from datetime import datetime, timedelta
import pandas as pd

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}

def fetch_flccim_events(url, start_date, end_date, calendar):
    start_ts = int(start_date.timestamp())
    end_ts = int(end_date.timestamp())

    params = {
        "rhc_action": "get_calendar_events",
        "post_type[]": "events",
        "calendar": calendar,
        "start": start_ts,
        "end": end_ts,
        "rhc_shrink": 1,
        "view": "month",
    }

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()


def process(config):
    print(f"Processing: {config['url']}")

    start_date = datetime.today()
    end_date = start_date + timedelta(days=60)

    # Fetch and parse
    json_data = fetch_flccim_events(config['url'], start_date, end_date, config['calendar'])
    events = json_data.get("EVENTS", [])
    final_events = []

    for event in events:
        # print (event)
        event_types = event.get("10")
        start_date_str = event.get("15")
        start_time_str = event.get("16", "00:00")
        end_date_str = event.get("17", start_date_str)
        end_time_str = event.get("18", "23:59")

        if start_date_str == "#" or end_date_str == "#":
            continue
        if start_time_str == "#":
            start_time_str = "00:00"
        if end_time_str == "#":
            end_time_str = "23:59"

        start_dt = datetime.strptime(f"{start_date_str} {start_time_str}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{end_date_str} {end_time_str}", "%Y-%m-%d %H:%M")

        if 289 in event_types or 645 in event_types:
            continue

        final_event = {
            "start_dt": start_dt,
            "end_dt": end_dt,
            "Event Title": event.get("3", "Unknown"),
            "Event Link": event.get("6", "TBD"),
            "Organizer": config["organizer"],
            "Industry": config["industry"],
            "Market": config["market"],
        }
        final_events.append(final_event)

    df = pd.DataFrame(final_events)
    print(df.to_string(index=False))

    return final_events
