
from langchain_core.prompts import ChatPromptTemplate

FLIGHTS_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a travel assistant. You have no live flight data, so give "
     "plausible estimates only. Keep prices realistic for the stated budget."
     "give all prices in {currency}"
     "Each option must cost no more than {max_per_person} {currency} per person."
     "If nothing realistic fits under that cap, return the cheapest realistic options anyway."
     "Do NOT invent unrealistically low prices."
     "Give a price range for ONE traveller. Do not state exact durations or flight times. "
     "Say that connections are likely when the origin is a smaller city."),
    ("human",
     "Suggest 2-3 flight options from {origin} to {destination}, "
     "departing {start_date} and returning {end_date} for {passengers} passenger(s) in {cabin_class} class. "
     "The total budget {budget} {currency} is for ALL travellers and the whole trip."
     "Do not invent exact departure or arrival times; give typical airlines, stops and duration only.."
     "Give the price estimate PER PERSON in {currency}."),
])
STAYS_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a travel assistant. You have no live accommodation data, so give "
     "plausible estimates only. Keep prices realistic for the stated budget."
     "give all prices in {currency}"
     "Each option must cost no more than {max_per_night} {currency} per room per night."
     "If nothing realistic fits under that cap, return the cheapest realistic options anyway."
     "Do NOT invent unrealistically low prices."),
    ("human",
     "Suggest 2-3 accommodation options in {destination} for {start_date} to {end_date}. "
     "Total trip budget is {budget} {currency}."
     "Tell the price per night in {currency} and one short highlight for each option."),
])
ACTIVITIES_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a travel assistant. You have no live activity data, so give "
     "plausible estimates only. Keep prices realistic for the stated budget."
     "give all prices in {currency}"
     "Each option must cost no more than {max_per_person} {currency} per person."
     "If nothing realistic fits under that cap, return the cheapest realistic options anyway."
     "Do NOT invent unrealistically low prices."),
    ("human",
     "Suggest 2-3 activities in {destination} for {start_date} to {end_date}. "
     "Total trip budget is {budget} {currency}."
     "Tell the prices per person and the approximate duration in hours for each activity."
     "give all the prices in {currency}"),
])
SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You write short, friendly day-by-day trip itineraries. Use ONLY the facts provided. "
     "Do not invent prices, flight times, restaurants, venues or attractions. "
     "Use the day labels given. Day 1 is arrival and the last day is departure, so keep them light. "
     "Put at most one major activity on a day, and treat an activity of 6 hours or more as a full day. "
     "If activities do not fill every day, say the remaining time is free to explore. "
     "Stay under 200 words. Plain text, one line per day."
     "Format every line exactly as 'Day N - Weekday DD Mon: ...'."
     "Use the flight times given. If the outbound flight arrives on a later date than it departs, say the traveller departs on that day and arrives on the arrival date, and do not describe sightseeing before arrival."
     "Do not add examples, show names, drinks, meals or any other detail that is not in the facts. "
     "Never write 'e.g.'."),
    ("human", "Facts:\n{facts}\n\nWrite the itinerary."),
])
