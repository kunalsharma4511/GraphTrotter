import json
from pathlib import Path

files = sorted((Path(__file__).parent / "results").glob("eval_*.json"))
for r in json.loads(files[-1].read_text(encoding="utf-8")):
    if r["snapshot"].get("itinerary"):
        print(f"=== {r['case']} ===\n{r['snapshot']['itinerary']}\n")