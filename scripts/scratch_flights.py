from travel_planner.schemas import TravelRequest
from travel_planner.nodes.flights import flights_node

req = TravelRequest(
    origin="Indore",
    destination="Paris",
    start_date="2026-12-01",
    end_date="2026-12-05",
    currency="INR",
    budget=300000,
    passengers=2,
    cabin_class="business",
)

result = flights_node({"request": req, "errors": []})
print(result)