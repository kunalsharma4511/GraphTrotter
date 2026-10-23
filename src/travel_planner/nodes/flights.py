
import os

from apify_client import ApifyClient

from travel_planner.config import get_llm
from travel_planner.prompts import FLIGHTS_PROMPT
from travel_planner.schemas import FlightsResult
from travel_planner.state import TravelState
from travel_planner import budget

from travel_planner.airports import resolve_airport
from travel_planner.schemas import LiveFlight
from travel_planner.state import TravelState

ACTOR = "tidyscrape/google-flights-scraper"
PRICE_COVERS_ALL_TRAVELLERS = True   # set True if the 1-vs-2 adults test shows the price doubling
CABIN_MAP = {                         # edit to the values your actor's input accepts
    "economy": "economy",
    "premium_economy": "premium-economy",
    "business": "business",
    "first": "first",
}


def _estimate_flights(req):
     # your existing LLM chain, returning result.flights
    structured = get_llm().with_structured_output(FlightsResult, method="json_schema")
    chain = (FLIGHTS_PROMPT | structured).with_retry(stop_after_attempt=3)
    result = chain.invoke({
        "origin": req.origin or "an unspecified city",
        "destination": req.destination,
        "start_date": str(req.start_date),
        "end_date": str(req.end_date),
        "currency": req.currency,
        "budget": req.budget,
        "passengers": req.passengers,
        "cabin_class": req.cabin_class.replace("_", " "),
        "max_per_person": int(req.budget * budget.SHARES["flights"] / req.passengers)
    })
    return result.flights


def _fetch_live(req) -> list[dict]:
    origin, dest = resolve_airport(req.origin), resolve_airport(req.destination)
    if not origin:
        raise ValueError(f"unknown or missing origin '{req.origin}' (try an airport code like IDR)")
    if not dest:
        raise ValueError(f"unknown destination '{req.destination}' (try an airport code like LHR)")
    run_input = {
        "routes": [f"{origin}-{dest}"],
        "departureDates": [str(req.start_date)],
        "returnDates": [str(req.end_date)],
        "currency": req.currency,
        "adults": req.passengers,
        "children": 0,
        "infantsInSeat": 0,
        "infantsOnLap": 0,
        "cabinClass": CABIN_MAP[req.cabin_class],
        "maxStops": "any",
        "language": "en",
        "maxResults": 6,
        "maxItemsPerSearch": 6,
        "maxReturnSearches": 1,
        "maxConcurrency": 2,
        "proxyConfiguration": {"useApifyProxy": True},
    }
    client = ApifyClient(os.environ["APIFY_TOKEN"])
    run = client.actor(ACTOR).call(run_input=run_input)
    dataset_id = run["defaultDatasetId"] if isinstance(run, dict) else run.default_dataset_id
    return list(client.dataset(dataset_id).iterate_items())


def _hours(minutes):
    return round((minutes or 0) / 60, 1)


def _to_live_flight(item: dict, req) -> LiveFlight:
    def per_person(x):
        if x is None:
            return None
        return x / req.passengers if PRICE_COVERS_ALL_TRAVELLERS else x

    layovers = item.get("layovers") or []
    note = "Direct" if not layovers else "via " + ", ".join(
        l.get("city") or l.get("airport", "?") for l in layovers
    )
    ret = item.get("returnFlight") or {}
    price = per_person(float(item["price"]))
    return LiveFlight(
        airline=" + ".join(item.get("airlines") or ["Unknown"]),
        price_min=price,
        price_max=price,
        route_note=note,
        stops=item.get("stops") or 0,
        duration_hours=_hours(item.get("durationMinutes")),
        departure_time=item.get("departureTime") or "",
        arrival_time=item.get("arrivalTime") or "",
        return_stops=ret.get("stops"),
        return_duration_hours=_hours(ret.get("durationMinutes")) if ret else None,
        return_departure_time=ret.get("departureTime"),
        return_arrival_time=ret.get("arrivalTime"),
        typical_low=per_person(item.get("typicalPriceLow")),
        typical_high=per_person(item.get("typicalPriceHigh")),
        price_level=item.get("priceLevel"),
        url=item.get("googleFlightsUrl"),
        scraped_at=item.get("scrapedAt"),
    )


def _pick_flights(items: list[dict]) -> list[dict]:
    usable = [i for i in items if i.get("price")]
    if not usable:
        return []
    cheapest = min(usable, key=lambda i: i["price"])
    best = next((i for i in usable if i.get("isBest")), usable[0])
    fastest = min(usable, key=lambda i: i.get("durationMinutes") or 10**9)
    picks, seen = [], set()
    for i in (cheapest, best, fastest):
        key = (tuple(i.get("flightNumbers") or []), i["price"])
        if key not in seen:
            seen.add(key)
            picks.append(i)
    return sorted(picks, key=lambda i: i["price"])


def flights_node(state: TravelState) -> dict:
    req = state["request"]
    try:
        picks = _pick_flights(_fetch_live(req))
        if picks:
            return {"flights": [_to_live_flight(i, req) for i in picks]}
        reason = "no live fares returned"
    except Exception as e:
        reason = str(e)
    try:  # fall back to clearly labelled AI estimates
        return {
            "flights": _estimate_flights(req),
            "errors": [f"flights: live fares unavailable ({reason}); showing AI estimates"],
        }
    except Exception as e:
        return {"errors": [f"flights: {reason}; estimate also failed: {e}"]}
