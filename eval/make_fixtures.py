import json
from pathlib import Path

results = Path(__file__).parent / "results"
out = Path(__file__).parent / "fixtures"
out.mkdir(exist_ok=True)

saved = {}
for f in sorted(results.glob("eval_*.json")):          # oldest first, so newer runs overwrite
    for r in json.loads(f.read_text(encoding="utf-8")):
        snap = r.get("snapshot") or {}
        if snap.get("facts"):
            saved[r["case"]] = {"case": r["case"], "facts": snap["facts"]}

for case, data in saved.items():
    (out / f"{case}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("saved", case)
print(len(saved), "fixture(s) in", out)