from travel_planner.graph import graph
from travel_planner.schemas import TravelRequest

req = TravelRequest(
    origin="Indore",
    destination="London",
    start_date="2026-12-01",
    end_date="2026-12-05",
    currency="INR",
    budget=300000,
    passengers=2,
    # rooms=1,
    cabin_class="economy",
)

result = graph.invoke(
    {"request": req, "errors": []},
    config={
        "run_name": "plan_trip",
        "tags": ["demo"],
        "metadata": {"destination": req.destination, "passengers": req.passengers},
    },
)
print("FLIGHTS:")
for f in result.get("flights", []):
    print("  ", f)

print("STAYS:")
for s in result.get("stays", []):
    print("  ", s)

print("ACTIVITIES:")
for a in result.get("activities", []):
    print("  ", a)

print("ERRORS:", result.get("errors", []))


from travel_planner import budget
summary = budget.estimate_total(
    req, result.get("flights", []), result.get("stays", []), result.get("activities", [])
)
print(summary)

