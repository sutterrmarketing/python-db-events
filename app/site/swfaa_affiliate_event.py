import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time
import pandas as pd
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}


def get_event_list(config):
    print(f"[INFO] Fetching from: {config['url']}")
    response = requests.get(config["url"], headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")
    events = []

    event_blocks = soup.select(config["event_list_selector"])
    if not event_blocks:
        print("[WARN] No event blocks found.")
        return []

    for block in event_blocks:
        try:
            # Get title & URL
            link_tag = block.select_one(config["event_link_selector"])
            title = link_tag.get_text(strip=True)
            url = urljoin(config["base_url"], link_tag.get("href"))

            # Start datetime
            start_elem = block.select_one(
                config["detail_selectors"]["DateTime"]["start_selector"]
            )
            start_raw = start_elem.get(
                config["detail_selectors"]["DateTime"]["start_attribute"], ""
            )
            start_dt = datetime.strptime(
                start_raw.replace("Starts ", ""), "%B %d, %Y at %I:%M %p"
            )

            # Default end datetime same as start
            end_dt = start_dt

            # Try to extract explicit end datetime
            end_selector = config["detail_selectors"]["DateTime"].get("end_selector")
            end_elem = block.select_one(end_selector) if end_selector else None

            if end_elem:
                try:
                    end_raw = end_elem.get(config["detail_selectors"]["DateTime"]["end_attribute"], "")
                    end_dt = datetime.strptime(end_raw.replace("Ends ", ""), "%B %d, %Y at %I:%M %p")
                except Exception as e:
                    print(f"[WARN] Failed to parse end datetime: {e}")
                    end_dt = start_dt
            else:
                # Fall back to parsing time range string
                time_spans = block.select("span.c-event-date-stub__time")
                if time_spans:
                    time_text = time_spans[0].get_text(strip=True)
                    if "-" in time_text:
                        try:
                            _, end_time_str = [t.strip() for t in time_text.split("-")]
                            end_dt = datetime.combine(start_dt.date(), datetime.strptime(end_time_str, "%I:%M %p").time())
                        except Exception as e:
                            print(f"[WARN] Failed to parse end time string: {e}")
                            end_dt = start_dt

            events.append(
                {
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                    "Event Title": title,
                    "Event Link": url,
                    "Organizer": config.get("organizer", ""),
                    "Industry": config.get("industry", ""),
                    "Market": config.get("market", ""),
                }
            )

        except Exception as e:
            print(f"[ERROR] Skipping event block due to error: {e}")
            continue

    time.sleep(config.get("scraper_interval", 1))

    return events


def process(config):
    event_list = get_event_list(config)
    if not event_list:
        print("[INFO] No events found.")
        return []

    df = pd.DataFrame(event_list)
    print(df.to_string(index=False))
    return event_list
