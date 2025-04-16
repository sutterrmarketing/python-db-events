import requests
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}

def build_crewnetwork_url(base_url, days_ahead=60):
    today = datetime.today().date()
    future = today + timedelta(days=days_ahead)
    return f"{base_url}?minEndDate={today}&maxEndDate={future}"


def get_event_list(config):
    url = build_crewnetwork_url(config["url"])
    url2 = config["url2"]
    base_url = config["base_url"]
    interval = config.get("scraper_interval", 1)
    time.sleep(interval)

    print(f"Fetching events from: {url}")

    # Step 1: Get storyblok_events mapping from url2
    print(f"Fetching slug map from: {url2}")
    response2 = requests.get(url2, headers=headers)
    soup = BeautifulSoup(response2.text, "html.parser")

    script_tag = soup.find("script", id="__NEXT_DATA__", type="application/json")
    if not script_tag:
        print("[ERROR] Could not find __NEXT_DATA__ script tag.")
        return []

    data = json.loads(script_tag.string)
    slug_map = {}
    try:
        events_list = data["props"]["pageProps"]["pageProps"]["story"]["content"][
            "page_template"
        ][0]["storyblok_events"]
        slug_map = {
            item["netforum_event_id"]: item["full_slug"] for item in events_list
        }
    except Exception as e:
        print(f"[ERROR] Failed to parse storyblok_events: {e}")

    time.sleep(interval)
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    all_events = response.json()
    filter_chapters = set(config.get("event_type_selector", []))

    final_events = []

    for item in all_events:
        if item.get("chapter") not in filter_chapters:
            continue

        title = item.get("title", "Untitled").strip()

        netforum_event_id = item.get("netforumId")

        full_slug = slug_map.get(netforum_event_id)
        trimmed_slug = "/" + "/".join(full_slug.strip("/").split("/")[2:])

        if trimmed_slug:
            link = f"{base_url}{trimmed_slug}"
        else:
            link = item.get("registrationUrl") or None

        start_raw = item.get("startDateTime")
        end_raw = item.get("endDateTime")

        try:
            start_dt = datetime.fromisoformat(start_raw)
            end_dt = datetime.fromisoformat(end_raw)
        except Exception as e:
            print(f"[ERROR] Failed to parse datetime: {e}")
            continue

        event_data = {
            "start_dt": start_dt,
            "end_dt": end_dt,
            "Event Title": title,
            "Event Link": "https://crewnetwork.org/join/crew-sarasota-manatee",
            "Organizer": config.get("organizer"),
            "Industry": config.get("industry"),
            "Market": config.get("market"),
        }

        final_events.append(event_data)

    return final_events


def process(config):
    event_list = get_event_list(config)
    print(f"Collected {len(event_list)} events")

    if event_list:
        df = pd.DataFrame(event_list)
        print(df.to_string(index=False))
        return event_list

    return []
