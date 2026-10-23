import math

from travel_planner.schemas import TravelRequest

SHARES = {"flights": 0.40, "stays": 0.40, "activities": 0.20}
BREAKUP_NOTE = (
    "This price breakup covers only flights, stay and activities. "
    "Food, local transport, visa and similar expenses are excluded."
)
HOTEL_NOTE = (
    "Hotel prices come from Booking.com at the time of search and exclude taxes and fees "
    "(for example, city tourist tax), so the final price will be somewhat higher. "
    "Check the booking link for the exact amount."
)
def nights(req: TravelRequest) -> int:
    return max((req.end_date - req.start_date).days, 1)


def rooms(req: TravelRequest) -> int:
    return math.ceil(req.passengers / 2)


def flight_cap_per_person(req: TravelRequest) -> int:
    return int(req.budget * SHARES["flights"] / req.passengers)


def activity_cap_per_person(req: TravelRequest) -> int:
    return int(req.budget * SHARES["activities"] / req.passengers)


def estimate_total(req, flights, stays, activities) -> dict:
    flights_low = min((f.price_min for f in flights), default=0) * req.passengers
    flights_high = min((f.price_max for f in flights), default=0) * req.passengers
    stays_total = min((s.total_price for s in stays), default=0)
    activities_total = sum(a.price_estimate for a in activities) * req.passengers

    low = flights_low + stays_total + activities_total
    high = flights_high + stays_total + activities_total
    return {
        "flights": (flights_low, flights_high),
        "stays": stays_total,
        "activities": activities_total,
        "total_low": low,
        "total_high": high,
        "over_by_low": max(low - req.budget, 0),
        "over_by_high": max(high - req.budget, 0),
    }