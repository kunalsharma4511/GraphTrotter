from travel_planner.faithfulness import check_itinerary

FACTS = """Destination: London
Travellers: 2 (economy class)
Trip days: Day 1 = Mon 07 Dec, Day 2 = Tue 08 Dec, Day 3 = Wed 09 Dec
Flight (live fare): Air India + SWISS, 116,706 to 116,706 INR per person round trip (via Mumbai)
Outbound flight: departs 2026-12-07 19:50, arrives 2026-12-08 08:05 (local times)
Hotel (live price): ibis London City - Shoreditch, guest score 8.1/10, 97,832 INR total before taxes
Activity (AI estimate): Tower of London Guided Tour, about 3 h, 3,500 INR per person. Guided tour"""

GOOD = """Day 1 - Mon 07 Dec: Depart on Air India + SWISS at 19:50. No sightseeing before arrival.
Day 2 - Tue 08 Dec: Arrive in London at 08:05. Check in to ibis London City - Shoreditch. Free time.
Day 3 - Wed 09 Dec: Tower of London Guided Tour (about 3 h, 3,500 INR per person)."""


def test_a_faithful_itinerary_passes():
    report = check_itinerary(GOOD, FACTS)
    assert report.passed
    assert report.names == []
    assert report.score == 1.0
    assert report.checked > 0


def test_invented_price_is_caught():
    bad = GOOD + "\nDay 3 - Wed 09 Dec: Dinner cruise (5,000 INR)."
    report = check_itinerary(bad, FACTS)
    assert "5000" in report.numbers
    assert not report.passed


def test_invented_time_is_caught():
    report = check_itinerary(GOOD + "\nDinner at 21:30.", FACTS)
    assert "21:30" in report.times


def test_invented_date_is_caught():
    report = check_itinerary(GOOD + "\nDay 4 - Tue 15 Dec: Free day.", FACTS)
    assert "15 Dec" in report.dates


def test_invented_venue_is_reported_as_a_name():
    report = check_itinerary(GOOD + "\nVisit Buckingham Palace.", FACTS)
    assert "Buckingham Palace" in report.names
    assert report.passed  # names are soft: they warn but do not fail


def test_day_numbers_and_dates_are_not_treated_as_prices():
    report = check_itinerary("Day 2 - Tue 08 Dec: Free day.", FACTS)
    assert report.numbers == []


def test_empty_itinerary_scores_one():
    assert check_itinerary("", FACTS).score == 1.0