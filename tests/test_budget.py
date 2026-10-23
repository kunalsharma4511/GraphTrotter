from travel_planner import budget
from travel_planner.schemas import Activity, FlightOption, StayOption, TravelRequest


def make_request(**overrides):
    data = dict(
        destination="Paris",
        start_date="2026-12-01",
        end_date="2026-12-05",  # 4 nights
        currency="INR",
        budget=300000,
        passengers=2,
    )
    data.update(overrides)
    return TravelRequest(**data)


FLIGHTS = [
    FlightOption(airline="A", price_min=60000, price_max=80000, route_note="x"),
    FlightOption(airline="B", price_min=50000, price_max=90000, route_note="x"),
]
STAYS = [
    StayOption(name="H1", area="a", total_price=90000, price_per_night=22500),
    StayOption(name="H2", area="b", total_price=120000, price_per_night=30000),
]
ACTIVITIES = [
    Activity(name="A1", description="d", price_estimate=2000, duration_hours=2),
    Activity(name="A2", description="d", price_estimate=3500, duration_hours=3),
]


def test_nights():
    assert budget.nights(make_request()) == 4


def test_nights_never_below_one():
    assert budget.nights(make_request(end_date="2026-12-01")) == 1


def test_rooms_two_travellers_per_room():
    assert [budget.rooms(make_request(passengers=n)) for n in (1, 2, 3, 4, 5)] == [1, 1, 2, 2, 3]


def test_estimate_total_hand_calculated():
    out = budget.estimate_total(make_request(), FLIGHTS, STAYS, ACTIVITIES)
    # flights: cheapest min 50,000 x 2 = 100,000 ; cheapest max 80,000 x 2 = 160,000
    # stays: cheapest total 90,000
    # activities: (2,000 + 3,500) x 2 = 11,000
    assert out["flights"] == (100000, 160000)
    assert out["stays"] == 90000
    assert out["activities"] == 11000
    assert out["total_low"] == 201000
    assert out["total_high"] == 261000
    assert out["over_by_low"] == 0
    assert out["over_by_high"] == 0


def test_over_budget_amounts():
    out = budget.estimate_total(make_request(budget=200000), FLIGHTS, STAYS, ACTIVITIES)
    assert out["over_by_low"] == 1000    # 201,000 - 200,000
    assert out["over_by_high"] == 61000  # 261,000 - 200,000


def test_single_traveller_halves_flights_and_activities():
    out = budget.estimate_total(make_request(passengers=1), FLIGHTS, STAYS, ACTIVITIES)
    assert out["flights"] == (50000, 80000)
    assert out["activities"] == 5500


def test_empty_results_give_zero_not_a_crash():
    out = budget.estimate_total(make_request(), [], [], [])
    assert out["total_low"] == 0
    assert out["total_high"] == 0