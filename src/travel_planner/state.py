"""

TODO: define TravelState(TypedDict):
  request    : TravelRequest
  flights    : list[FlightOption]
  stays      : list[StayOption]
  activities : list[Activity]
  errors     : Annotated[list[str], operator.add]   # reducer so parallel nodes can all append

Why: three parallel nodes each write their OWN key, so no conflicts.
Only `errors` is written by several nodes, which is why it needs a reducer.
"""
import operator
from typing import Annotated
from typing import Annotated, TypedDict
from travel_planner.schemas import Activity, FlightOption, StayOption, TravelRequest
class TravelState(TypedDict):
  request    : TravelRequest
  flights    : list[FlightOption]
  stays      : list[StayOption]
  activities : list[Activity]
  errors     : Annotated[list[str], operator.add]   # reducer so parallel nodes can all append
  summary    : str



