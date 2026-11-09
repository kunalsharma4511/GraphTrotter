"""Compare itinerary prompt variants on frozen fixtures.
Costs only model calls (no scraping). Run from the project root:

    python eval/prompt_eval.py --runs 3
    python eval/prompt_eval.py --runs 2 --variants v1_current,v2_strict
"""
import argparse
import json
import statistics
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402

from travel_planner.config import get_llm  # noqa: E402
from travel_planner.faithfulness import check_itinerary  # noqa: E402
from travel_planner.prompts import SUMMARY_PROMPT  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
RESULTS = Path(__file__).parent / "results"

NAIVE = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful travel assistant."),
    ("human", "Write an exciting day-by-day itinerary for this trip.\n\n{facts}"),
])

STRICT = ChatPromptTemplate.from_messages([
    ("system",
     "You write short day-by-day trip itineraries from a fixed list of facts.\n"
     "Rules:\n"
     "1. Use ONLY information in the facts. Every price, time, date, hotel and activity you "
     "mention must appear in the facts, copied exactly.\n"
     "2. Do not add place names, attractions, restaurants, shows, meals, transfers, weather "
     "or opinions that are not in the facts.\n"
     "3. Format every line exactly as: Day N - Weekday DD Mon: text\n"
     "4. If the outbound flight arrives on a later date than it departs, the departure day "
     "has no sightseeing and the arrival day starts at the arrival time given.\n"
     "5. Never write 'e.g.'. Under 200 words. Plain text, one line per day."),
    ("human", "Facts:\n{facts}\n\nWrite the itinerary."),
])

VARIANTS = {"v0_naive": NAIVE, "v1_current": SUMMARY_PROMPT, "v2_strict": STRICT}


def load_fixtures() -> list[dict]:
    files = sorted(FIXTURES.glob("*.json"))
    if not files:
        raise SystemExit("No fixtures found. Run: python eval/make_fixtures.py")
    return [json.loads(f.read_text(encoding="utf-8")) for f in files]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3, help="generations per fixture per variant")
    parser.add_argument("--variants", default=",".join(VARIANTS))
    args = parser.parse_args()

    names = [v.strip() for v in args.variants.split(",") if v.strip()]
    unknown = [n for n in names if n not in VARIANTS]
    if unknown:
        raise SystemExit(f"Unknown variant(s): {unknown}. Choose from {list(VARIANTS)}")

    fixtures = load_fixtures()
    total_calls = len(fixtures) * len(names) * args.runs
    print(f"{len(fixtures)} fixture(s) x {len(names)} variant(s) x {args.runs} run(s) = {total_calls} model calls.")
    if input("Continue? [y/N] ").strip().lower() != "y":
        return 0

    llm = get_llm()
    records = []
    for variant in names:
        chain = VARIANTS[variant] | llm | StrOutputParser()
        for fx in fixtures:
            for run in range(args.runs):
                rec = {"variant": variant, "fixture": fx["case"], "run": run}
                try:
                    text = chain.invoke({"facts": fx["facts"]}).strip()
                    rep = check_itinerary(text, fx["facts"])
                    rec.update(text=text, passed=rep.passed, score=rep.score,
                               hard=rep.hard_failures, names=rep.names, checked=rep.checked)
                except Exception as e:                       # a failed call is recorded, not fatal
                    rec.update(error=repr(e))
                records.append(rec)
                time.sleep(0.5)                              # be gentle with rate limits

    print(f"\n{'variant':<12} {'runs':>5} {'pass':>6} {'mean score':>11} {'unsupported':>12} {'names/run':>10} {'errors':>7}")
    summary = {}
    for variant in names:
        ok = [r for r in records if r["variant"] == variant and "error" not in r]
        errors = sum(1 for r in records if r["variant"] == variant and "error" in r)
        if not ok:
            print(f"{variant:<12} no successful runs ({errors} errors)")
            continue
        passed = sum(1 for r in ok if r["passed"])
        mean_score = statistics.mean(r["score"] for r in ok)
        unsupported = sum(len(r["hard"]) for r in ok)
        names_per_run = statistics.mean(len(r["names"]) for r in ok)
        summary[variant] = dict(runs=len(ok), passed=passed, mean_score=round(mean_score, 3),
                                unsupported=unsupported, names_per_run=round(names_per_run, 2), errors=errors)
        print(f"{variant:<12} {len(ok):>5} {passed:>3}/{len(ok):<2} {mean_score:>11.3f} "
              f"{unsupported:>12} {names_per_run:>10.2f} {errors:>7}")

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"prompt_eval_{datetime.now():%Y%m%d_%H%M%S}.json"
    out.write_text(json.dumps({"summary": summary, "records": records}, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())