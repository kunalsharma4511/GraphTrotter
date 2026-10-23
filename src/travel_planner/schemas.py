"""
TODO (pydantic.BaseModel):
  TravelRequest : origin (optional), destination, start_date, end_date, budget (float > 0)
  FlightOption  : airline, departure_time, arrival_time, price_estimate_inr
  StayOption    : name, area, price_per_night_inr, highlights
  Activity      : name, description, price_estimate_inr, duration_hours
  FlightsResult / StaysResult / ActivitiesResult : each wraps a list of the above
                  (the LLM returns these via llm.with_structured_output(...))
"""
import math
from datetime import date
from math import ceil
from typing import Optional, Literal

from pydantic import BaseModel, Field, model_validator


class TravelRequest(BaseModel):
    origin: Optional[str] = Field(None, description="City the traveller departs from")
    destination: str = Field(description="City or country to visit")
    start_date: date
    end_date: date
    currency: str = Field("USD", description="Currency code for the budget, e.g. USD or INR")
    budget: float = Field(gt=0, description="Total trip budget in {currency}")
    passengers: int = Field(1, ge=1, le=9, description="Number of travellers (default 1)")
    cabin_class: Literal["economy", "premium economy", "business", "first"] = "economy"

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self
    def check_price_range(self):
        if self.price_min > self.price_max:
            raise ValueError("price_min must be <= price_max")
        return self



class FlightOption(BaseModel):
    airline: str = Field(description="Airline commonly flying this route (or via a hub)")
    price_min: float = Field(ge=0, description="Low end of typical round-trip price PER PERSON in the requested cabin")
    price_max: float = Field(ge=0, description="High end of typical round-trip price PER PERSON in the requested cabin")
    route_note: str = Field(description="One short line, e.g. likely connection city. Do not state exact stops or duration.")

    @model_validator(mode="after")
    def fix_price_range(self):
        if self.price_min > self.price_max:
            self.price_min, self.price_max = self.price_max, self.price_min
        return self

class LiveFlight(FlightOption):
    #A real fare. price_min == price_max == price PER PERSON, round trip.
    live: bool = True
    stops: int = 0
    duration_hours: float = 0
    departure_time: str = ""
    arrival_time: str = ""
    return_stops: Optional[int] = None
    return_duration_hours: Optional[float] = None
    return_departure_time: Optional[str] = None
    return_arrival_time: Optional[str] = None
    typical_low: Optional[float] = None
    typical_high: Optional[float] = None
    price_level: Optional[str] = None
    url: Optional[str] = None
    scraped_at: Optional[str] = None

class FlightsResult(BaseModel):
    flights: list[FlightOption] = Field(description="2-3 illustrative flight options")

class StayOption(BaseModel):
    name: str
    area: str
    total_price: float
    price_per_night: float
    review_score: Optional[float] = None
    url: Optional[str] = None
    free_cancellation: bool = False


class StaysResult(BaseModel):
    stays: list[StayOption] = Field(description="2-3 illustrative accommodation options")


class Activity(BaseModel):
    name: str = Field(description="Name of the activity or attraction")
    description: str = Field(description="One or two sentences on what it involves")
    price_estimate: float = Field(ge=0, description="Approximate cost per person in {currency}")
    duration_hours: float = Field(gt=0, description="Typical time needed, in hours")


class ActivitiesResult(BaseModel):
    activities: list[Activity] = Field(description="2-3 illustrative activities")
