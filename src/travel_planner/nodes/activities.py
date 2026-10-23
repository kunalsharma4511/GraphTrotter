
from travel_planner.state import TravelState


import math

from travel_planner.config import get_llm
from travel_planner.prompts import ACTIVITIES_PROMPT
from travel_planner.schemas import ActivitiesResult, StaysResult
from travel_planner.state import TravelState
from travel_planner import budget


def activities_node(state: TravelState) -> dict:
    req = state["request"]
    try:
        structured = get_llm().with_structured_output(ActivitiesResult, method="json_schema")
        chain = (ACTIVITIES_PROMPT | structured).with_retry(stop_after_attempt=3)
        result = chain.invoke({
            "destination": req.destination,
            "start_date": str(req.start_date),
            "end_date": str(req.end_date),
            "budget": req.budget,
            "currency": req.currency,
            "passengers": req.passengers,
            "rooms": math.ceil(req.passengers / 2),
            "max_per_person": int(req.budget * budget.SHARES["activities"] / req.passengers)
        })
        return {"activities": result.activities}
    except Exception as e:
        return {"errors": [f"activities: {e}"]}
