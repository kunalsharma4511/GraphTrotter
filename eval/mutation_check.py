import json
from pathlib import Path

from travel_planner.faithfulness import check_itinerary

files = sorted((Path(__file__).parent / "results").glob("eval_*.json"))
data = json.loads(files[-1].read_text(encoding="utf-8"))
snap = next(r["snapshot"] for r in data if r["snapshot"].get("itinerary") and r["snapshot"].get("facts"))
itin, facts = snap["itinerary"], snap["facts"]

mutations = {
    "baseline (unchanged)": itin,
    "fake price": itin + "\nDinner cruise costs 7,777 INR per person.",
    "fake time": itin + "\nThe show starts at 21:45.",
    "fake date": itin + "\nDay 9 - Tue 22 Dec: Free day.",
    "fake venue": itin + "\nVisit Buckingham Palace.",
}
for name, text in mutations.items():
    r = check_itinerary(text, facts)
    print(f"{name:22} passed={r.passed}  hard={r.hard_failures}  names={r.names}")