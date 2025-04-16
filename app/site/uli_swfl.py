import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time
import random
import pandas as pd
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}

def get_event_list(config):

    time.sleep(config.get("scraper_interval", 1))
    base_url = config.get("base_url", "")

    current_year = datetime.now().year
    api_url = f"{config['url'].rstrip('/')}/{current_year}"
    print(f"[INFO] Fetching from: {api_url}")

    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"[ERROR] Failed to fetch or parse data: {e}")
        return []

    events = []

    program_filter = config.get("program_filter", None)
    type_filter = config.get("type_filter", None)

    for event in data.get("events", []):
        try:
            title = event.get("Event_Title", "").strip()
            registration_url = event.get("Registrant_List_Link", "").strip()
            event_id = event.get("Event_Id", "").strip()

            if event_id:
                url = f"{base_url}/uli-southwest-florida-webinars-events/detail/{event_id}"
            else:
                url = registration_url

            # Combine date and time
            start_dt_str = (
                event.get("Start_Date", "")[:10]
                + " "
                + event.get("Start_Time", "12:00 AM")
            )
            end_dt_str = (
                event.get("End_Date", "")[:10] + " " + event.get("End_Time", "11:59 PM")
            )

            start_dt = datetime.strptime(start_dt_str, "%Y-%m-%d %I:%M %p")
            end_dt = datetime.strptime(end_dt_str, "%Y-%m-%d %I:%M %p")

            event_program = event.get("Event_Programs", "").strip()
            event_type = event.get("Event_Types", "").strip()
            event_city = event.get("City", "").strip()

            event_market = config.get("market", "").strip()
            event_organizer = config.get("organizer", "").strip()

            if event_city.lower()=="tampa":
                event_organizer = "ULI TB"
                event_market = "TPA"
            if event_city.lower()=="orlando":
                event_organizer = "ULI CF"
                event_market = "ORL"

            if any(word.lower() in title.lower() for word in ["uli southwest florida"]):
                event_organizer = "ULI SWFL"
                event_market = "SWFL"
                continue

            if event_program.lower() in program_filter:
                print(
                    f"[INFO] Skipping event because of event program is {event_program} : {url}"
                )
                continue
            if event_type.lower() in type_filter:
                print(
                    f"[INFO] Skipping event because of event type is {event_type} : {url}"
                )
                continue

            events.append(
                {
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                    "Event Title": title,
                    "Event Link": url,
                    "Organizer": event_organizer,
                    "Industry": config["industry"],
                    "Market": event_market,
                }
            )

        except Exception as e:
            print(f"[ERROR] Skipping event due to error: {e}")
            continue

    return events


def process(config):
    event_list = get_event_list(config)
    if not event_list:
        print("[INFO] No events found.")
        return []

    df = pd.DataFrame(event_list)
    print(df.to_string(index=False))
    return event_list
