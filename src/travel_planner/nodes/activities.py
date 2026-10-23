"""STEP 7 - The activities node.

TODO:
  def activities_node(state: TravelState) -> dict:
      1. build chain = ACTIVITIES_PROMPT | get_llm().with_structured_output(ActivitiesResult)
      2. result = chain.invoke({...fields from state["request"]...})
      3. return {"activities": result.activities}
      4. wrap in try/except -> return {"errors": [f"activities: {e}"]} so one failure
         doesn't kill the whole trip plan

Tip: 7-8B local models can fail structured output. Fallback: ask for JSON text and
parse it yourself, or retry once.
"""
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