import json
from pathlib import Path

from travel_planner.faithfulness import check_itinerary

files = sorted((Path(__file__).parent / "results").glob("eval_*.json"))
for r in json.loads(files[-1].read_text(encoding="utf-8")):
    snap = r["snapshot"]
    if not snap.get("itinerary") or not snap.get("facts"):
        continue
    rep = check_itinerary(snap["itinerary"], snap["facts"])
    print(f"{r['case']}: score {rep.score:.2f}, unsupported {rep.hard_failures}, names {rep.names}")