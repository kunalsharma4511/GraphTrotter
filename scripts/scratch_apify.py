import os

from apify_client import ApifyClient
from dotenv import load_dotenv

from travel_planner.nodes import stays
from travel_planner.nodes.stays import MIN_SCORE

load_dotenv()
client = ApifyClient(os.environ["APIFY_TOKEN"])


def fetch(rooms: int) -> list[dict]:
    run_input = {
        "destination": "Paris",
        "destType": "CITY",
        "checkin": "2026-12-01",
        "checkout": "2026-12-05",
        "adults": 2,
        "children": 0,
        "rooms": rooms,
        "currency": "INR",
        "sortBy": "POPULARITY",
        "maxResults": 8,
    }
    run = client.actor("santamaria-automations/booking-com-scraper").call(run_input=run_input)
    dataset_id = run["defaultDatasetId"] if isinstance(run, dict) else run.default_dataset_id
    return list(client.dataset(dataset_id).iterate_items())

# def _is_rated(h: dict) -> bool:
#     score = h.get("review_score")
#     return score is not None and score > 0

# ok = [
#     h for h in stays.hotels
#     if h.get("price") and not h.get("is_sold_out") and _is_rated(h) and h["review_score"] >= MIN_SCORE
# ]

for rooms in (1, 2):
    items = fetch(rooms)
    print(f"\n--- rooms={rooms}: {len(items)} hotels ---")
    for h in items[:8]:
        print(
            h.get("name"), "|", h.get("district"), "|",
            h.get("price"), h.get("currency"),
            "| per night:", h.get("price_per_night"),
            "| score:", h.get("review_score"),
            "| sold out:", h.get("is_sold_out"),
        )