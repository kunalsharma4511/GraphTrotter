from travel_planner.schemas import FlightOption

f = FlightOption(airline="Test", price_min=90000, price_max=50000, route_note="via Doha")
print(f.price_min, f.price_max)   # swap version: 50000.0 90000.0