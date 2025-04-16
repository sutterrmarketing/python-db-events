import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import pandas as pd
import time
import json
import html, re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}


def extract_jsonld_event(soup):
    """Clean and safely parse JSON-LD script containing event info."""
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        raw = script.string
        if not raw or "@type" not in raw or "Event" not in raw:
            continue

        try:
            # Step 1: Decode HTML entities (&ldquo;, &rdquo;, etc.)
            clean_text = html.unescape(raw)

            # Step 2: Remove newlines inside strings (commonly in "description")
            clean_text = re.sub(
                r"(?<!\\)\\n", " ", clean_text
            )  # sanitize any literal "\n"
            clean_text = re.sub(r"[\r\n]+", " ", clean_text)  # strip real newlines

            # Step 3: Parse JSON safely
            data = json.loads(clean_text)

            # Step 4: Return the first Event object
            if isinstance(data, list):
                for obj in data:
                    if obj.get("@type") == "Event":
                        return obj
            elif isinstance(data, dict) and data.get("@type") == "Event":
                return data

        except Exception as e:
            print(f"[WARN] Failed to parse cleaned JSON-LD: {e}")
            continue

    return {}


def get_event_details(event_url):

    try:
        response = requests.get(event_url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")
        jsonld = extract_jsonld_event(soup)

        start_str = jsonld.get("startDate")
        end_str = jsonld.get("endDate")

        if not start_str or not end_str:
            return {}

        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)

        return {"start_dt": start_dt, "end_dt": end_dt}


    except Exception as e:
        print(f"[ERROR] Detail fetch failed for {event_url}: {e}")
        return {}


def get_event_list(config):
    print(f"Fetching events from: {config['url']}")
    response = requests.get(config["url"], headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    for row in soup.select(config["event_list_selector"]):
        tds = row.find_all("td", class_="data_row")
        if len(tds) < 1:
            continue

        title_tag = tds[0].select_one("div b a")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        url = urljoin(config["base_url"], title_tag.get("href"))

        # Visit detail page for accurate datetime
        time.sleep(config.get("scraper_interval", 1))
        details = get_event_details(url)
        if not details:
            continue

        events.append(
            {
                "Event Title": title,
                "Event Link": url,
                **details,
                "Organizer": config["organizer"],
                "Industry": config["industry"],
                "Market": config["market"],
            }
        )

    time.sleep(config.get("scraper_interval", 1))

    return events


def process(config):
    event_list = get_event_list(config)
    print(f"Collected {len(event_list)} valid events")
    if event_list:
        df = pd.DataFrame(event_list)
        print(df.to_string(index=False))
        return event_list
    return []
