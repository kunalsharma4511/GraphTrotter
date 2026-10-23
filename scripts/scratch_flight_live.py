import os

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
client = ApifyClient(os.environ["APIFY_TOKEN"])


def fetch(adults, route="IDR-LON"):
    run_input = {
        "routes": [route],
        "departureDates": ["2026-12-01"],
        "returnDates": ["2026-12-05"],
        "currency": "INR",
        "adults": adults,
        "children": 0,
        "infantsInSeat": 0,
        "infantsOnLap": 0,
        "cabinClass": "business",
        "maxStops": "any",
        "language": "en",
        "maxResults": 5,
        "maxItemsPerSearch": 5,
        "maxReturnSearches": 1,
        "maxConcurrency": 2,
        "proxyConfiguration": {"useApifyProxy": True},
    }
    run = client.actor("tidyscrape/google-flights-scraper").call(run_input=run_input)
    dataset_id = run["defaultDatasetId"] if isinstance(run, dict) else run.default_dataset_id
    return list(client.dataset(dataset_id).iterate_items())


def show(title, items):
    print(f"\n--- {title}: {len(items)} itineraries ---")
    for i in items:
        print(i["price"], i["currency"], "|", i["airlines"], "| stops", i["stops"],
              "| dest", i["destination"], "| typical", i.get("typicalPriceLow"), "-", i.get("typicalPriceHigh"))


for adults in (1, 2):
    show(f"adults={adults}, IDR-LON", fetch(adults))

show("adults=1, IDR-LHR", fetch(1, "IDR-LHR"))