
import os

from apify_client import ApifyClient

from travel_planner import budget
from travel_planner.schemas import StayOption
from travel_planner.state import TravelState

ACTOR = "santamaria-automations/booking-com-scraper"
MIN_SCORE = 7.5


def _fetch_hotels(req) -> list[dict]:
    client = ApifyClient(os.environ["APIFY_TOKEN"])
    run_input = {
        "destination": req.destination,
        "destType": "CITY",
        "checkin": str(req.start_date),
        "checkout": str(req.end_date),
        "adults": req.passengers,
        "children": 0,
        "rooms": budget.rooms(req),
        "currency": req.currency,
        "sortBy": "POPULARITY",
        "maxResults": 8,
    }
    run = client.actor(ACTOR).call(run_input=run_input)
    dataset_id = run["defaultDatasetId"] if isinstance(run, dict) else run.default_dataset_id
    return list(client.dataset(dataset_id).iterate_items())


def _pick(hotels: list[dict], cap: float) -> tuple[list[dict], bool]:
    ok = [
        h for h in hotels
        if h.get("price") and not h.get("is_sold_out") and (h.get("review_score") or 0) >= MIN_SCORE
    ]
    pool = [h for h in ok if h["price"] <= cap]
    fits = bool(pool)
    pool = pool or ok
    if not pool:
        return [], False
    by_price = sorted(pool, key=lambda h: h["price"])
    candidates = [by_price[0], by_price[len(by_price) // 2], max(pool, key=lambda h: h["review_score"])]
    picks, seen = [], set()
    for h in candidates:
        key = h.get("id") or h["name"]
        if key not in seen:
            seen.add(key)
            picks.append(h)
    return picks, fits



def stays_node(state: TravelState) -> dict:
    req = state["request"]
    try:
        hotels = _fetch_hotels(req)
        cap = req.budget * budget.SHARES["stays"]
        picks, fits = _pick(hotels, cap)
        if not picks:
            return {"errors": ["stays: no available hotels matched the filters"]}
        nights = budget.nights(req)
        stays = [
            StayOption(
                name=h["name"],
                area=h.get("district") or h.get("location") or req.destination,
                total_price=h["price"],
                price_per_night=h.get("price_per_night") or h["price"] / nights,
                review_score=h.get("review_score"),
                url=h.get("url"),
                free_cancellation=bool(h.get("free_cancellation")),
            )
            for h in picks
        ]
        out = {"stays": stays}
        if not fits:
            out["errors"] = ["stays: nothing fit your stay budget share, showing the cheapest well-rated options"]
        return out
    except Exception as e:
        return {"errors": [f"stays: {e}"]}
