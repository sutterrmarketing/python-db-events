import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
import urllib.parse
import pandas as pd
import time 
import pytz


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Encoding": "identity",
}

def build_calendar_url(base_url, start: datetime, end: datetime) -> str:

    # Format the datetime: "YYYY-MM-DD HH:MM:SS.mmm"
    start_str = start.strftime("%Y-%m-%d %H:%M:%S.000")
    end_str = end.strftime("%Y-%m-%d %H:%M:%S.000")

    # URL encode the parameters (e.g., space -> %20)
    params = {
        "startdate": start_str,
        "enddate": end_str,
        "_": str(int(datetime.now().timestamp() * 1000)),  # timestamp in ms
    }

    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    full_url = f"{base_url}?{query_string}"

    return full_url


def get_event_list(config):
    """Fetch the list of events from the API calendar feed."""
    start_date = datetime.today()
    end_date = start_date + timedelta(days=30)

    api_url = build_calendar_url(config["url"], start_date, end_date)
    print(f"Fetching events from {api_url}")

    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching events from {api_url}: {e}")
        return []

    content = response.content
    if content.startswith(b"\xef\xbb\xbf"):
        content = content[3:]

    soup = BeautifulSoup(content, "xml")
    events_xml = soup.find_all("newCalendarDatav3")

    if not events_xml:
        print(f"No events found for {config.get('name', config['url'])}")
        return []

    events = []
    for item in events_xml:
        title = item.find("title").text.strip() if item.find("title") else "N/A"
        if title.startswith("Fort Myers") or title.startswith("Ft Myers"):
            organizer = "ABC SWFL"
            market = "SWFL"
        else:
            organizer = "ABC TB"
            market = "TPA"

        event_type = (
            item.find("EventType").text.strip() if item.find("EventType") else "N/A"
        )
        if event_type == "Educational Event":
            continue

        start_dt_str = (
            item.find("StartDateTimeUtc").text
            if item.find("StartDateTimeUtc")
            else None
        )
        end_dt_str = (
            item.find("EndDateTimeUtc").text if item.find("EndDateTimeUtc") else None
        )

        try:
            start_dt_utc = datetime.fromisoformat(start_dt_str)
            end_dt_utc = datetime.fromisoformat(end_dt_str)
        except Exception as e:
            print(f"[ERROR] Failed to parse datetime: {e}")
            continue

        eastern = pytz.timezone("America/New_York")
        start_dt = start_dt_utc.astimezone(eastern)
        end_dt = end_dt_utc.astimezone(eastern)

        event_id = (item.find("id").text if item.find("id") else "")

        if event_id != "" and title != "":
            event_link = urljoin(
                "https://web.abcflgulf.org/events/", f"{title}-{event_id}/details"
            )
        else:
            event_link = (
                item.find("registrationUrl").text.strip()
                if item.find("registrationUrl") and item.find("registrationUrl").text
                else config["url"]
            )

        events.append(
            {
                "Weekday": start_dt.strftime("%A"),
                "start_dt": start_dt,
                "end_dt": end_dt,
                "Event Title": title,
                "Event Link": event_link,
                "Organizer": organizer,
                "Industry": config["industry"],
                "Market": market,
            }
        )

    time.sleep(config.get("scraper_interval", 1))  # polite delay
    return events

def process(config):
    print(f"Processing: {config['url']}")
    event_list = get_event_list(config)
    print(f"Found {len(event_list)} events")
    df = pd.DataFrame(event_list)
    print(df.to_string(index=False))  # Display in terminal
    return event_list
