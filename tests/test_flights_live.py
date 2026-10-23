from langchain_core.runnables import RunnableLambda

from travel_planner.nodes import flights as flights_mod
from travel_planner.schemas import FlightOption, TravelRequest

RAW = [
    {"price": 120000, "airlines": ["A"], "flightNumbers": ["A1"], "stops": 1, "durationMinutes": 900,
     "departureTime": "2026-12-01T10:00", "arrivalTime": "2026-12-01T22:00", "layovers": [{"city": "Delhi"}]},
    {"price": 90000, "airlines": ["B"], "flightNumbers": ["B1"], "stops": 2, "durationMinutes": 1300,
     "departureTime": "2026-12-01T11:00", "arrivalTime": "2026-12-02T09:00", "layovers": []},
]


def make_req(**kw):
    data = dict(origin="Indore", destination="London", start_date="2026-12-01",
                end_date="2026-12-05", currency="INR", budget=300000, passengers=1)
    data.update(kw)
    return TravelRequest(**data)


def test_picks_include_cheapest_and_are_sorted():
    picks = flights_mod._pick_flights(RAW)
    assert [p["price"] for p in picks] == sorted(p["price"] for p in picks)
    assert picks[0]["price"] == 90000


def test_conversion_sets_live_fields():
    f = flights_mod._to_live_flight(RAW[0], make_req())
    assert f.live is True
    assert f.price_min == f.price_max == 120000
    assert f.stops == 1 and f.duration_hours == 15
    assert f.route_note == "via Delhi"


def test_direct_flight_note():
    assert flights_mod._to_live_flight(RAW[1], make_req()).route_note == "Direct"


def test_price_split_when_actor_returns_party_total(monkeypatch):
    monkeypatch.setattr(flights_mod, "PRICE_COVERS_ALL_TRAVELLERS", True)
    f = flights_mod._to_live_flight(RAW[0], make_req(passengers=2))
    assert f.price_min == 60000


def test_live_failure_falls_back_to_estimates(monkeypatch):
    def boom(_req):
        raise RuntimeError("apify down")

    est = [FlightOption(airline="X", price_min=1, price_max=2, route_note="est")]
    monkeypatch.setattr(flights_mod, "_fetch_live", boom)
    monkeypatch.setattr(flights_mod, "_estimate_flights", lambda _req: est)
    out = flights_mod.flights_node({"request": make_req(), "errors": []})
    assert out["flights"] == est
    assert "live fares unavailable" in out["errors"][0]


def test_unknown_city_reports_clear_reason(monkeypatch):
    monkeypatch.setattr(flights_mod, "_estimate_flights", lambda _req: [])
    out = flights_mod.flights_node({"request": make_req(destination="Atlantis"), "errors": []})
    assert "unknown destination" in out["errors"][0]