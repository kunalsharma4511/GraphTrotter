"""STEP 10 - CLI runner to test the graph without a UI.

TODO: build a TravelRequest, call graph.invoke({"request": req, "errors": []}),
pretty-print flights / stays / activities / errors.
Try graph.stream(..., stream_mode="updates") to watch nodes finish.
"""

from pydantic import ValidationError

from travel_planner import budget
from travel_planner.graph import graph
from travel_planner.schemas import TravelRequest


def ask(prompt: str, default: str | None = None) -> str | None:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def read_request() -> TravelRequest:
    """Keep asking until the input passes TravelRequest validation."""
    while True:
        try:
            return TravelRequest(
                origin=ask("Origin city (optional)"),
                destination=ask("Destination"),
                start_date=ask("Start date (YYYY-MM-DD)"),
                end_date=ask("End date (YYYY-MM-DD)"),
                currency=ask("Currency", "INR"),
                budget=ask("Total budget"),
                passengers=ask("Passengers", "1"),
                cabin_class=ask(
                    "Cabin class (economy / premium_economy / business / first)",
                    "economy",
                ),
            )
        except ValidationError as err:
            print("\nPlease fix the following and try again:")
            for e in err.errors():
                field = ".".join(str(p) for p in e["loc"]) or "request"
                print(f"  - {field}: {e['msg']}")
            print()


def print_results(req: TravelRequest, result: dict) -> None:
    cur = req.currency
    flights = result.get("flights", [])
    stays = result.get("stays", [])
    activities = result.get("activities", [])

    print("\n=== FLIGHTS (round trip, per person) ===")
    for f in flights:
        print(f"  {getattr(f, 'airline', 'N/A')}: {getattr(f, 'price_min', 0):,.0f} to {getattr(f, 'price_max', 0):,.0f} {cur}  ({getattr(f, 'route_note', '')})")

    print("\n=== STAYS (per room, per night) ===")
    for s in stays:
        print(f"  {s.name} - {s.area}: {s.price_per_night:,.0f} {cur}")
        print(f"      {s.highlights}")

    print("\n=== ACTIVITIES (per person) ===")
    for a in activities:
        print(f"  {a.name}: {a.price_estimate:,.0f} {cur}, about {a.duration_hours:g} h")
        print(f"      {a.description}")

    summary = budget.estimate_total(req, flights, stays, activities)
    print("\n=== ESTIMATED COST ===")
    print(f"  Total: {summary['total_low']:,.0f} to {summary['total_high']:,.0f} {cur}")
    print(f"  Budget: {req.budget:,.0f} {cur}")
    if summary["over_by_low"] > 0:
        print(f"  WARNING: about {summary['over_by_low']:,.0f} {cur} over budget.")
    print(f"  Note: {budget.BREAKUP_NOTE}")
    print("  These are estimates. Check airline and hotel sites for real prices and availability.")

    if result.get("summary"):
        print("\n=== ITINERARY (AI-written from the results above) ===")
        print(result["summary"])
        
    errors = result.get("errors", [])
    if errors:
        print("\n=== PROBLEMS ===")
        for e in errors:
            print(f"  - {e}")


def main() -> None:
    print("Travel Planner\n")
    req = read_request()
    print("\nPlanning your trip, this can take a little while...")
    result = graph.invoke(
    {"request": req, "errors": []},
    config={
        "run_name": "plan_trip",
        "tags": ["demo"],
        "metadata": {"destination": req.destination, "passengers": req.passengers},
    },
)
    print_results(req, result)


if __name__ == "__main__":
    main()