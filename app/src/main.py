import importlib
import urllib3
import asyncio
from src.utils import deduplicate_events, load_config
from app.src.weblist import weblist

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

async def run_all():
    for site in weblist:
        try:
            print(f"Processing site: {site}")
            config = load_config(site)
            module = importlib.import_module(f"app.site.{site}")
            events_raw = module.process(config)
            events = deduplicate_events(events_raw)

        except Exception as e:
            print(f"Failed to process {site}: {e}")

if __name__ == "__main__":
    asyncio.run(run_all())