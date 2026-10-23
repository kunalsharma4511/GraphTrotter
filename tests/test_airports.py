from travel_planner.airports import resolve_airport


def test_known_city():
    assert resolve_airport("Indore") == "IDR"


def test_case_and_spaces():
    assert resolve_airport("  london ") == "LHR"


def test_city_with_country():
    assert resolve_airport("Paris, France") == "CDG"


def test_code_passthrough():
    assert resolve_airport("lhr") == "LHR"


def test_city_name_beats_code_guess():
    assert resolve_airport("Goa") == "GOI"  # not read as the code "GOA"


def test_unknown_and_empty():
    assert resolve_airport("Atlantis") is None
    assert resolve_airport("") is None
    assert resolve_airport(None) is None