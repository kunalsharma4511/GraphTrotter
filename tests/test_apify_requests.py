from travel_planner.nodes import flights as flights_mod
from travel_planner.nodes import stays as stays_mod
from travel_planner.schemas import TravelRequest


class FakeActor:
    def __init__(self, store):
        self.store = store

    def call(self, run_input=None, **kwargs):
        self.store["input"] = run_input
        return {"defaultDatasetId": "ds"}


class FakeDataset:
    def __init__(self, items):
        self.items = items

    def iterate_items(self):
        return iter(self.items)


class FakeApify:
    def __init__(self, store, items):
        self.store, self.items = store, items

    def actor(self, name):
        self.store["actor"] = name
        return FakeActor(self.store)

    def dataset(self, dataset_id):
        return FakeDataset(self.items)


def make_req(**kw):
    data = dict(origin="Indore", destination="London", start_date="2026-12-01",
                end_date="2026-12-05", currency="INR", budget=300000, passengers=2)
    data.update(kw)
    return TravelRequest(**data)


def test_flights_request_is_built_correctly(monkeypatch):
    store = {}
    monkeypatch.setenv("APIFY_TOKEN", "test")
    monkeypatch.setattr(flights_mod, "ApifyClient", lambda token: FakeApify(store, [{"price": 1}]))
    items = flights_mod._fetch_live(make_req(cabin_class="business"))
    sent = store["input"]
    assert sent["routes"] == ["IDR-LHR"]          # adjust if you mapped London to a city code
    assert sent["adults"] == 2
    assert sent["cabinClass"] == flights_mod.CABIN_MAP["business"]
    assert sent["departureDates"] == ["2026-12-01"]
    assert sent["returnDates"] == ["2026-12-05"]
    assert sent["currency"] == "INR"
    assert items == [{"price": 1}]


def test_hotels_request_is_built_correctly(monkeypatch):
    store = {}
    monkeypatch.setenv("APIFY_TOKEN", "test")
    monkeypatch.setattr(stays_mod, "ApifyClient", lambda token: FakeApify(store, [{"name": "H"}]))
    items = stays_mod._fetch_hotels(make_req(passengers=3))
    sent = store["input"]
    assert sent["adults"] == 3
    assert sent["rooms"] == 2                      # 3 travellers need 2 rooms
    assert sent["currency"] == "INR"
    assert sent["checkin"] == "2026-12-01" and sent["checkout"] == "2026-12-05"
    assert items == [{"name": "H"}]