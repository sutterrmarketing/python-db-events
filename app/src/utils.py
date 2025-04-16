import json
import os

CONFIG_DIR = "app/config"

def deduplicate_events(events):
    seen = set()
    unique_events = []

    for event in events:
        key = (
            event.get("Event Title", "").strip().lower(),
            event.get("Event Link", "").strip().lower(),
        )
        if key not in seen:
            seen.add(key)
            unique_events.append(event)
        else:
            print(f"🗑️ Duplicate skipped: {key[0]}")

    return unique_events


def load_config(site_name):
    config_path = os.path.join(CONFIG_DIR, f"{site_name}.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Config file for {site_name} not found at {config_path}"
        )
    with open(config_path, "r") as f:
        return json.load(f)
