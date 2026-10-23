"""STEP 6 + 8 - Wire the graph.

TODO:
  from langgraph.graph import StateGraph, START, END
  builder = StateGraph(TravelState)
  builder.add_node("flights", flights_node) ... stays, activities
  fan-out : START -> flights, START -> stays, START -> activities   (run in parallel)
  fan-in  : each of the three -> END  (or -> "summarize" -> END)
  graph = builder.compile()

Build order suggestion: first wire ONLY flights (START -> flights -> END) and test it,
then add the other two, then the fan-out.
`graph` must be a module-level variable (langgraph.json points to it).
"""


from langgraph.graph import END, START, StateGraph

from travel_planner.nodes.activities import activities_node
from travel_planner.nodes.flights import flights_node
from travel_planner.nodes.stays import stays_node
from travel_planner.state import TravelState
from travel_planner.nodes.summarize import summarize_node

builder = StateGraph(TravelState)
builder.add_node("flights", flights_node)
builder.add_node("stays", stays_node)
builder.add_node("activities", activities_node)
builder.add_node("summarize", summarize_node)

for name in ("flights", "stays", "activities"):
    builder.add_edge(START, name)   # fan-out: all three run in parallel
  
builder.add_edge(["flights", "stays", "activities"], "summarize")  # fan-in to summarize node
builder.add_edge("summarize", END)

graph = builder.compile()