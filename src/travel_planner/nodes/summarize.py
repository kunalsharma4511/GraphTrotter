
from datetime import timedelta

from langchain_core.output_parsers import StrOutputParser

from travel_planner.config import get_llm
from travel_planner.prompts import SUMMARY_PROMPT
from travel_planner.state import TravelState


def build_facts(req, flights, stays, activities) -> str:
    """Assemble the facts in plain code so the model never has to calculate or guess."""
    n_days = (req.end_date - req.start_date).days + 1
    days = [req.start_date + timedelta(days=i) for i in range(n_days)]
    lines = [
        f"Destination: {req.destination}",
        f"Travellers: {req.passengers} ({req.cabin_class.replace('_', ' ')} class)",
        "Trip days: " + ", ".join(f"Day {i} = {d:%a %d %b}" for i, d in enumerate(days, 1)),
    ]
    if flights:
        f = min(flights, key=lambda x: x.price_min)
        label = "live fare" if getattr(f, "live", False) else "AI estimate"
        lines.append(
            f"Flight ({label}): {f.airline}, {f.price_min:,.0f} to {f.price_max:,.0f} "
            f"{req.currency} per person round trip ({f.route_note})"
        )
        if getattr(f, "live", False) and f.departure_time:
            lines.append(
                f"Outbound flight: departs {f.departure_time.replace('T', ' ')}, "
                f"arrives {f.arrival_time.replace('T', ' ')} (local times)"
            )
            if f.return_departure_time:
                lines.append(
                    f"Return flight: departs {f.return_departure_time.replace('T', ' ')}, "
                    f"arrives {(f.return_arrival_time or '').replace('T', ' ')} (local times)"
                )
    if stays:
        rated = [s for s in stays if s.review_score]
        s = max(rated, key=lambda x: x.review_score) if rated else stays[0]
        score = f", guest score {s.review_score:.1f}/10" if s.review_score else ""
        lines.append(
            f"Hotel (live price): {s.name} in {s.area}{score}, "
            f"{s.total_price:,.0f} {req.currency} total before taxes"
        )
    for a in activities:
        lines.append(
            f"Activity (AI estimate): {a.name}, about {a.duration_hours:g} h, "
            f"{a.price_estimate:,.0f} {req.currency} per person. {a.description}"
        )
    return "\n".join(lines)


def summarize_node(state: TravelState) -> dict:
    req = state["request"]
    flights = state.get("flights", [])
    stays = state.get("stays", [])
    activities = state.get("activities", [])

    if not (flights or stays or activities):
        return {}  

    try:
        chain = SUMMARY_PROMPT | get_llm() | StrOutputParser()
        text = chain.invoke({"facts": build_facts(req, flights, stays, activities)})
        return {"summary": text.strip()}
    except Exception as e:
        return {"errors": [f"summary: {e}"]}
