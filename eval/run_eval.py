"""Live evaluation: runs real trips through the real graph and checks the results.

COSTS MONEY (Apify runs + Groq calls) and needs a network connection.
Run it by hand from the project root:

    python eval/run_eval.py              # all cases
    python eval/run_eval.py --list       # show the cases
    python eval/run_eval.py --only business_2pax_over_budget,solo_economy
"""
import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from travel_planner import budget  # noqa: E402
from travel_planner.airports import resolve_airport  # noqa: E402
from travel_planner.graph import graph  # noqa: E402
from travel_planner.nodes.stays import MIN_SCORE  # noqa: E402
from travel_planner.schemas import TravelRequest  # noqa: E402

PASS, FAIL, WARN, SKIP = "PASS", "FAIL", "WARN", "SKIP"


# ------------------------------------------------------------------ cases
def trip(origin, destination, passengers, cabin, budget_amount):
    start = date.today() + timedelta(days=45)      # always in the future
    return dict(origin=origin, destination=destination, start_date=start,
                end_date=start + timedelta(days=4), currency="INR",
                budget=budget_amount, passengers=passengers, cabin_class=cabin)


CASES = [
    dict(name="economy_2pax_fits", request=trip("Indore", "London", 2, "economy", 500000),
         expect_over=False),
    dict(name="solo_economy", request=trip("Indore", "Paris", 1, "economy", 250000),
         expect_over=None),
    dict(name="three_pax_two_rooms", request=trip("Mumbai", "London", 3, "economy", 900000),
         expect_over=None),
    dict(name="business_2pax_over_budget", request=trip("Indore", "London", 2, "business", 300000),
         expect_over=True),
    dict(name="other_route_delhi_dubai", request=trip("Delhi", "Dubai", 2, "economy", 300000),
         expect_over=None),
    dict(name="unknown_city_rejected", guard=True),   # no paid call: checks the input guard only
]


# ------------------------------------------------------------------ checks
def check_guard():
    return [
        ("unknown city is rejected", PASS if resolve_airport("Atlantis") is None else FAIL, ""),
        ("known city resolves", PASS if resolve_airport("Indore") == "IDR" else FAIL, ""),
        ("airport code passes through", PASS if resolve_airport("lhr") == "LHR" else FAIL, ""),
    ]


def check_graph_case(case, req, state):
    checks = []
    errors = state.get("errors", [])
    flights, stays, acts = state.get("flights", []), state.get("stays", []), state.get("activities", [])
    summary_text = state.get("summary") or ""

    checks.append(("no errors reported", PASS if not errors else FAIL, "; ".join(errors)))
    for label, items in (("flights", flights), ("stays", stays), ("activities", acts)):
        checks.append((f"{label} returned", PASS if items else FAIL, f"{len(items)} item(s)"))

    # flights
    live = [f for f in flights if getattr(f, "live", False)]
    if flights:
        checks.append(("flights are live fares", PASS if len(live) == len(flights) else WARN,
                       "fell back to AI estimates" if not live else ""))
    with_range = [f for f in live if f.typical_high]
    if with_range:
        cheapest = min(f.price_min for f in live)
        ok = cheapest <= with_range[0].typical_high * 1.25
        checks.append(("cheapest fare near Google's typical range", PASS if ok else WARN,
                       f"{cheapest:,.0f} vs typical up to {with_range[0].typical_high:,.0f} per person"))
    else:
        checks.append(("cheapest fare near Google's typical range", SKIP, "no typical range returned"))

    # hotels
    nights = budget.nights(req)
    if stays:
        rated = all(s.review_score and s.review_score >= MIN_SCORE for s in stays)
        checks.append((f"hotels rated >= {MIN_SCORE}", PASS if rated else FAIL, ""))
        consistent = all(abs(s.price_per_night * nights - s.total_price) <= 0.02 * s.total_price
                         for s in stays)
        checks.append(("hotel night price x nights = total", PASS if consistent else FAIL, ""))

    # totals
    summary = budget.estimate_total(req, flights, stays, acts)
    if flights and stays and acts:
        exp_low = (min(f.price_min for f in flights) * req.passengers
                   + min(s.total_price for s in stays)
                   + sum(a.price_estimate for a in acts) * req.passengers)
        parts = sum([summary["flights"][0], summary["stays"], summary["activities"]])
        ok = abs(summary["total_low"] - exp_low) < 1 and abs(summary["total_low"] - parts) < 1
        checks.append(("total equals the sum of its parts", PASS if ok else FAIL,
                       f"total_low {summary['total_low']:,.0f}"))
        if case["expect_over"] is not None:
            over = summary["over_by_low"] > 0
            checks.append(("over-budget flag as expected",
                           PASS if over == case["expect_over"] else FAIL,
                           f"over_by_low {summary['over_by_low']:,.0f}, expected over={case['expect_over']}"))

    # itinerary
    if summary_text.strip():
        n_days = (req.end_date - req.start_date).days + 1
        missing = []
        for i in range(1, n_days + 1):
            label = f"{req.start_date + timedelta(days=i - 1):%a %d %b}"
            if f"Day {i}" not in summary_text and label not in summary_text:
                missing.append(i)
        checks.append(("itinerary covers every day", PASS if not missing else WARN,
                       f"missing day(s): {missing}" if missing else ""))
        checks.append(("itinerary has no 'e.g.' examples", WARN if "e.g." in summary_text else PASS, ""))

    snapshot = {
        "cheapest_flight_per_person": min((f.price_min for f in flights), default=None),
        "hotels": [s.name for s in stays],
        "total_low": summary["total_low"], "total_high": summary["total_high"],
        "over_by_low": summary["over_by_low"], "itinerary": summary_text,
        "activities": [{"name": a.name, "description": a.description} for a in acts],
    }
    return checks, snapshot


# ------------------------------------------------------------------ runner
def run_case(case):
    started = time.time()
    if case.get("guard"):
        return check_guard(), {}, time.time() - started
    req = TravelRequest(**case["request"])
    state = graph.invoke({"request": req, "errors": []},
                         config={"run_name": f"eval:{case['name']}", "tags": ["eval"]})
    checks, snapshot = check_graph_case(case, req, state)
    return checks, snapshot, time.time() - started


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--only", default="", help="comma-separated case names")
    args = parser.parse_args()

    if args.list:
        for c in CASES:
            print(c["name"], "(free)" if c.get("guard") else "(live)")
        return 0

    wanted = {n.strip() for n in args.only.split(",") if n.strip()}
    cases = [c for c in CASES if not wanted or c["name"] in wanted]
    live_count = sum(1 for c in cases if not c.get("guard"))
    print(f"About to run {live_count} LIVE case(s). Each calls Apify twice (flights + hotels) and Groq.")
    if input("Continue? [y/N] ").strip().lower() != "y":
        return 0

    results, any_fail = [], False
    for case in cases:
        print(f"\n=== {case['name']} ===")
        try:
            checks, snapshot, seconds = run_case(case)
        except Exception as e:  # a crash is a failed case, not a crashed eval
            checks, snapshot, seconds = [("case ran without crashing", FAIL, repr(e))], {}, 0.0
        for name, status, detail in checks:
            print(f"  [{status:<4}] {name}" + (f"  ({detail})" if detail else ""))
        print(f"  took {seconds:.1f}s")
        failed = any(s == FAIL for _, s, _ in checks)
        any_fail = any_fail or failed
        results.append({"case": case["name"], "seconds": round(seconds, 1), "passed": not failed,
                        "checks": [{"check": n, "status": s, "detail": d} for n, s, d in checks],
                        "snapshot": snapshot})

    passed = sum(1 for r in results if r["passed"])
    warns = sum(1 for r in results for c in r["checks"] if c["status"] == WARN)
    print(f"\n{passed} of {len(results)} cases passed all hard checks ({warns} warning(s)).")

    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"eval_{datetime.now():%Y%m%d_%H%M%S}.json"
    out.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}")
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())