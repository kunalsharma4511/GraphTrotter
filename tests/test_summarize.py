from travel_planner.nodes.summarize import build_facts
from travel_planner.schemas import Activity, FlightOption, StayOption, TravelRequest, LiveFlight

REQ = TravelRequest(destination="Paris", start_date="2026-12-01", end_date="2026-12-05",
                    currency="INR", budget=300000, passengers=2)
FLIGHTS = [FlightOption(airline="Air India", price_min=60000, price_max=80000, route_note="via Delhi")]
STAYS = [
    StayOption(name="Cheap", area="a", total_price=50000, price_per_night=12500, review_score=7.8),
    StayOption(name="Best", area="b", total_price=90000, price_per_night=22500, review_score=9.1),
]
ACTS = [Activity(name="Louvre", description="Guided tour", price_estimate=2000, duration_hours=3)]


def test_facts_contain_every_day_and_the_best_hotel():
    facts = build_facts(REQ, FLIGHTS, STAYS, ACTS)
    assert "Day 1 = Tue 01 Dec" in facts
    assert "Day 5 = Sat 05 Dec" in facts
    assert "Best in b" in facts and "Cheap" not in facts
    assert "Air India" in facts and "Louvre" in facts


def test_facts_work_with_missing_sections():
    facts = build_facts(REQ, [], [], [])
    assert "Destination: Paris" in facts
    assert "Hotel" not in facts


def test_live_flights_are_labelled_as_live_fares():
    live = [LiveFlight(airline="Air India", price_min=116706, price_max=116706, route_note="via Mumbai")]
    facts = build_facts(REQ, live, STAYS, ACTS)
    assert "Flight (live fare)" in facts
    assert "Flight (AI estimate)" not in facts