import json
from pathlib import Path

files = sorted(Path("eval/results").glob("prompt_eval_*.json"))
data = json.loads(files[-1].read_text(encoding="utf-8"))
for r in data["records"]:
    if r["variant"] == "v2_strict" and r.get("names"):
        print(r["fixture"], r["run"], r["names"])