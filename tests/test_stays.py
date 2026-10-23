from travel_planner.nodes.stays import _pick


def hotel(id_, name, price, score, sold_out=False):
    return {
        "id": id_, "name": name, "price": price, "review_score": score,
        "is_sold_out": sold_out, "district": "1st arr.",
    }


HOTELS = [
    hotel(1, "Good Hotel", 80000, 8.5),
    hotel(2, "Unrated Zero", 30000, 0),
    hotel(3, "Unrated None", 35000, None),
    hotel(4, "Sold Out", 40000, 9.0, sold_out=True),
    hotel(5, "Pricey Hotel", 200000, 9.2),
    hotel(6, "Low Score", 25000, 6.0),
]


def names(picks):
    return {h["name"] for h in picks}


def test_unrated_soldout_and_low_score_never_appear():
    picks, _ = _pick(HOTELS, cap=1_000_000)
    assert not names(picks) & {"Unrated Zero", "Unrated None", "Sold Out", "Low Score"}


def test_within_cap_is_preferred():
    picks, fits = _pick(HOTELS, cap=120000)
    assert fits is True
    assert names(picks) == {"Good Hotel"}


def test_falls_back_when_nothing_fits_the_cap():
    picks, fits = _pick(HOTELS, cap=10)
    assert fits is False
    assert names(picks) == {"Good Hotel", "Pricey Hotel"}


def test_no_valid_hotels_returns_empty():
    picks, fits = _pick([hotel(1, "Bad", 1000, 0)], cap=100000)
    assert picks == []
    assert fits is False


def test_no_duplicate_picks():
    picks, _ = _pick(HOTELS, cap=1_000_000)
    ids = [h["id"] for h in picks]
    assert len(ids) == len(set(ids))