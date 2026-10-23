"""STEP 12a - e.g. end_date before start_date must raise; negative budget must raise."""
import pytest
from pydantic import ValidationError

from travel_planner.schemas import FlightOption, TravelRequest


def make_request(**overrides):
    data = dict(
        destination="Paris",
        start_date="2026-12-01",
        end_date="2026-12-05",
        currency="INR",
        budget=300000,
        passengers=2,
        cabin_class="economy",
    )
    data.update(overrides)
    return TravelRequest(**data)


def test_valid_request():
    req = make_request()
    assert req.destination == "Paris"
    assert req.origin is None  # optional
    assert req.passengers == 2


def test_end_date_before_start_date_raises():
    with pytest.raises(ValidationError):
        make_request(start_date="2026-12-05", end_date="2026-12-01")


def test_same_day_trip_is_allowed():
    make_request(start_date="2026-12-01", end_date="2026-12-01")


@pytest.mark.parametrize("bad_budget", [0, -5])
def test_non_positive_budget_raises(bad_budget):
    with pytest.raises(ValidationError):
        make_request(budget=bad_budget)


@pytest.mark.parametrize("bad_count", [0, 10])
def test_passenger_limits(bad_count):
    with pytest.raises(ValidationError):
        make_request(passengers=bad_count)


def test_unknown_cabin_class_raises():
    with pytest.raises(ValidationError):
        make_request(cabin_class="luxury")


def test_reversed_flight_price_range_is_swapped():
    f = FlightOption(airline="X", price_min=90000, price_max=50000, route_note="via Delhi")
    assert f.price_min == 50000
    assert f.price_max == 90000


def test_correct_flight_price_range_is_unchanged():
    f = FlightOption(airline="X", price_min=50000, price_max=90000, route_note="via Delhi")
    assert (f.price_min, f.price_max) == (50000, 90000)