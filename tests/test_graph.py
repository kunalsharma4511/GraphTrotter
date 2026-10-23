"""STEP 12b - test the graph WITHOUT a real LLM.

Tip: monkeypatch get_llm (or each node) with a fake that returns fixed objects,
then assert all three keys are filled and that one failing node only adds to `errors`.
"""

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from travel_planner.graph import graph
from travel_planner.schemas import (
    ActivitiesResult,
    Activity,
    FlightOption,
    FlightsResult,
    TravelRequest,
)


class FakeLLM:
    """Stands in for get_llm() in the structured-output nodes."""

    def __init__(self, result):
        self.result = result

    def with_structured_output(self, schema, **kwargs):
        return RunnableLambda(lambda _: self.result)


class BrokenLLM:
    """Every call fails, to test graceful degradation."""

    def with_structured_output(self, schema, **kwargs):
        def boom(_):
            raise RuntimeError("model down")

        return RunnableLambda(boom)


def fake_summary_llm():
    # The summarize node calls the model directly (plain text, no structured output).
    return RunnableLambda(lambda _: AIMessage(content="Fake itinerary"))


def fake_hotels(_req):
    return [
        {
            "id": 1,
            "name": "Test Hotel",
            "district": "1st arr.",
            "price": 90000,
            "price_per_night": 22500,
            "review_score": 8.5,
            "is_sold_out": False,
            "url": "https://example.com",
            "free_cancellation": True,
        }
    ]

FAKE_RAW_FLIGHTS = [{
    "price": 116706, "airlines": ["Air India", "SWISS"], "flightNumbers": ["AI 2750"],
    "stops": 2, "durationMinutes": 1065, "departureTime": "2026-12-01T19:50",
    "arrivalTime": "2026-12-02T08:05", "isBest": True,
    "layovers": [{"city": "Mumbai", "airport": "BOM"}],
    "typicalPriceLow": 69000, "typicalPriceHigh": 115000, "priceLevel": "high",
}]

@pytest.fixture
def req():
    return TravelRequest(
        destination="Paris",
        start_date="2026-12-01",
        end_date="2026-12-05",
        currency="INR",
        budget=300000,
        passengers=2,
    )


def patch_all(monkeypatch):
    flights = FlightsResult(
        flights=[FlightOption(airline="X", price_min=60000, price_max=80000, route_note="via Delhi")]
    )
    acts = ActivitiesResult(
        activities=[Activity(name="A", description="d", price_estimate=2000, duration_hours=2)]
    )
    monkeypatch.setattr("travel_planner.nodes.flights.get_llm", lambda: FakeLLM(flights))
    monkeypatch.setattr("travel_planner.nodes.activities.get_llm", lambda: FakeLLM(acts))
    monkeypatch.setattr("travel_planner.nodes.stays._fetch_hotels", fake_hotels)
    monkeypatch.setattr("travel_planner.nodes.summarize.get_llm", fake_summary_llm)
    monkeypatch.setattr("travel_planner.nodes.flights._fetch_live", lambda _req: FAKE_RAW_FLIGHTS)


def run(req):
    return graph.invoke({"request": req, "errors": []})


def test_all_nodes_fill_state(monkeypatch, req):
    patch_all(monkeypatch)
    out = run(req)
    assert out["flights"] and out["stays"] and out["activities"]
    assert out["summary"] == "Fake itinerary"
    assert out["errors"] == []


def test_stays_failure_does_not_kill_the_rest(monkeypatch, req):
    patch_all(monkeypatch)

    def boom(_req):
        raise RuntimeError("apify down")

    monkeypatch.setattr("travel_planner.nodes.stays._fetch_hotels", boom)
    out = run(req)
    assert out["flights"] and out["activities"]
    assert not out.get("stays")
    assert any(e.startswith("stays") for e in out["errors"])
    assert out["summary"] == "Fake itinerary"  # still written from what exists


def test_flights_failure_is_isolated(monkeypatch, req):
    patch_all(monkeypatch)
    def boom(_req):
        raise RuntimeError("apify down")

    monkeypatch.setattr("travel_planner.nodes.flights._fetch_live", boom)
    monkeypatch.setattr("travel_planner.nodes.flights.get_llm", lambda: BrokenLLM())
    out = run(req)
    assert out["stays"] and out["activities"]
    assert not out.get("flights")
    assert any(e.startswith("flights") for e in out["errors"])


def test_no_summary_when_every_source_fails(monkeypatch, req):
    patch_all(monkeypatch)

    def boom(_req):
        raise RuntimeError("apify down")

    # Flights: the live source fails AND the LLM fallback fails.
    monkeypatch.setattr("travel_planner.nodes.flights._fetch_live", boom)
    monkeypatch.setattr("travel_planner.nodes.flights.get_llm", lambda: BrokenLLM())
    # Activities: the LLM fails.
    monkeypatch.setattr("travel_planner.nodes.activities.get_llm", lambda: BrokenLLM())
    # Stays: the scraper fails.
    monkeypatch.setattr("travel_planner.nodes.stays._fetch_hotels", boom)

    out = run(req)
    assert not out.get("summary")
    assert len(out["errors"]) == 3


def test_summary_failure_is_reported_not_raised(monkeypatch, req):
    patch_all(monkeypatch)

    def boom(_):
        raise RuntimeError("model down")

    monkeypatch.setattr("travel_planner.nodes.summarize.get_llm", lambda: RunnableLambda(boom))
    out = run(req)
    assert out["flights"] and out["stays"] and out["activities"]
    assert any(e.startswith("summary") for e in out["errors"])


def test_live_flights_are_used_when_available(monkeypatch, req):
    patch_all(monkeypatch)
    out = run(req)
    assert getattr(out["flights"][0], "live", False) is True
    assert out["errors"] == []


def test_flights_fall_back_to_estimates_when_live_fails(monkeypatch, req):
    patch_all(monkeypatch)

    def boom(_req):
        raise RuntimeError("apify down")

    monkeypatch.setattr("travel_planner.nodes.flights._fetch_live", boom)
    out = run(req)
    assert out["flights"]  # the FakeLLM estimate from patch_all
    assert not getattr(out["flights"][0], "live", False)
    assert any("live fares unavailable" in e for e in out["errors"])