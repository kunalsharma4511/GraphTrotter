
import datetime as dt
from datetime import datetime
import streamlit as st
from pydantic import ValidationError

from travel_planner import budget
from travel_planner.graph import graph
from travel_planner.schemas import TravelRequest
from travel_planner.airports import resolve_airport

from pathlib import Path
from PIL import Image

LOGO = Path(__file__).parent / "docs" / "logo.png"

st.set_page_config(
    page_title="GraphTrotter",
    page_icon=Image.open(LOGO),
    layout="wide",
)

CABINS = {
    "Economy": "economy",
    "Premium economy": "premium_economy",
    "Business": "business",
    "First": "first",
}
CURRENCIES = ["INR", "USD", "EUR", "GBP"]


def money(value: float, currency: str) -> str:
    return f"{value:,.0f} {currency}"

def fmt_ts(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%d %b %Y, %H:%M UTC")
    except Exception:
        return ts or "just now"

# ---------------------------------------------------------------- input form
c_logo, c_title = st.columns([1, 9])
c_logo.image(str(LOGO), width=72)
c_title.title("GraphTrotter")
st.caption("Flights and Hotels are live prices from Booking.com." \
" Activities are AI estimates. Check official sites for real prices and availability.")

with st.form("trip_form"):
    c1, c2 = st.columns(2)
    origin = c1.text_input("Origin city (optional)", placeholder="e.g. Indore")
    destination = c2.text_input("Destination", placeholder="e.g. Paris")

    c3, c4 = st.columns(2)
    start = dt.date.today() + dt.timedelta(days=30)
    start_date = c3.date_input("Start date", value=start)
    end_date = c4.date_input("End date", value=start + dt.timedelta(days=4))

    c5, c6, c7, c8 = st.columns(4)
    currency = c5.selectbox("Currency", CURRENCIES)
    trip_budget = c6.number_input("Total budget", min_value=1000, value=300000, step=5000)
    passengers = c7.number_input("Passengers", min_value=1, max_value=9, value=2)
    cabin_label = c8.selectbox("Cabin class", list(CABINS))

    submitted = st.form_submit_button("Plan my trip", type="primary")

# ---------------------------------------------------------------- run graph
if submitted:
    if not resolve_airport(origin) or not resolve_airport(destination):
        st.error("Enter name of the city or 3-letter IATA code")
        st.stop()
    try:
        req = TravelRequest(
            origin=origin.strip() or None,
            destination=destination.strip(),
            start_date=start_date,
            end_date=end_date,
            currency=currency,
            budget=trip_budget,
            passengers=passengers,
            cabin_class=CABINS[cabin_label],
        )
    except ValidationError as err:
        st.session_state.pop("result", None)
        for e in err.errors():
            field = ".".join(str(p) for p in e["loc"]) or "request"
            st.error(f"{field}: {e['msg']}")
    else:
        with st.spinner("Planning your trip. Live hotel prices can take up to a minute..."):
            result = graph.invoke(
                {"request": req, "errors": []},
                config={
                    "run_name": "plan_trip",
                    "tags": ["demo"],
                    "metadata": {"destination": req.destination, "passengers": req.passengers},
                },
            )
        st.session_state["result"] = {"req": req, "state": result}

# ---------------------------------------------------------------- results
saved = st.session_state.get("result")
if saved:
    req: TravelRequest = saved["req"]
    state = saved["state"]
    cur = req.currency
    flights = state.get("flights", [])
    stays = state.get("stays", [])
    activities = state.get("activities", [])
    errors = state.get("errors", [])

    st.divider()
    st.subheader(f"{req.destination.title()}: {req.start_date:%d %b} to {req.end_date:%d %b %Y}")
    st.caption(
        f"{req.passengers} traveller(s), {req.cabin_class.replace('_', ' ')} class, "
        f"{budget.rooms(req)} room(s), {budget.nights(req)} night(s)"
    )

    for message in errors:
        st.warning(message)

    # ---- cost summary
    summary = budget.estimate_total(req, flights, stays, activities)
    total_text = (
        money(summary["total_low"], cur)
        if round(summary["total_low"]) == round(summary["total_high"])
        else f"{money(summary['total_low'], cur)} to {money(summary['total_high'], cur)}"
    )
    m1, m2 = st.columns(2)
    m1.metric("Estimated total", total_text)
    m2.metric("Your budget", money(req.budget, cur))

    missing = [name for name, items in
               (("flights", flights), ("stays", stays), ("activities", activities)) if not items]

    if missing:
        st.warning(f"The total above leaves out: {', '.join(missing)} (no results returned).")
    elif summary["over_by_low"] > 0:
        st.error(f"Even the cheapest combination is about {money(summary['over_by_low'], cur)} over budget.")
    elif summary["over_by_high"] > 0:
        st.info(f"Could exceed your budget by up to {money(summary['over_by_high'], cur)}.")
    else:
        st.success("This plan fits within your budget (before the exclusions below).")
    st.caption(budget.BREAKUP_NOTE)

    tab_flights, tab_stays, tab_activities, tab_plan = st.tabs(["✈️ Flights", "🏨 Stays", "🎟️ Activities",  "🗓️ Itinerary"])

    # ---- flights
    with tab_flights:
        live_flights = [f for f in flights if getattr(f, "live", False)]
        if live_flights:
            st.caption(f"Live fares from Google Flights, fetched {live_flights[0].scraped_at or 'just now'}. Prices change often.")
        else:
            st.caption("AI estimates, not live fares. Check airline sites for routes, durations and exact prices.")
        for f in flights:
            with st.container(border=True):
                st.markdown(f"**{f.airline}**")
                if getattr(f, "live", False):
                    st.write(f"{money(f.price_min, cur)} per person round trip "
                             f"({money(f.price_min * req.passengers, cur)} for {req.passengers})")
                    st.write(f"Outbound: {f.departure_time.replace('T', ' ')} to {f.arrival_time.replace('T', ' ')} "
                             f"· {f.duration_hours:g} h · {f.stops} stop(s) · {f.route_note}")
                    if f.return_departure_time:
                        st.write(f"Return: {f.return_departure_time.replace('T', ' ')} to "
                                 f"{(f.return_arrival_time or '').replace('T', ' ')} · "
                                 f"{f.return_duration_hours:g} h · {f.return_stops} stop(s)")
                    if f.typical_low and f.typical_high:
                        st.caption(f"Google rates this fare as {f.price_level}. Typical for this route: "
                                   f"{money(f.typical_low, cur)} to {money(f.typical_high, cur)} per person.")
                    if f.url:
                        st.markdown(f"[View on Google Flights]({f.url})")
                else:
                    st.write(f"{money(f.price_min, cur)} to {money(f.price_max, cur)} per person (round trip), "
                             f"about {money(f.price_min * req.passengers, cur)} to "
                             f"{money(f.price_max * req.passengers, cur)} for {req.passengers}")
                    st.caption(f.route_note)
        if not flights:
            st.write("No flights available.")

    # ---- stays
    with tab_stays:
        st.caption("Live prices from Booking.com when you searched.")
        st.caption(budget.HOTEL_NOTE)
        for s in stays:
            with st.container(border=True):
                st.markdown(f"**{s.name}** · {s.area}")
                score = f"⭐ {s.review_score:.1f}/10 · " if s.review_score else ""
                cancel = " · Free cancellation" if s.free_cancellation else ""
                st.write(
                    f"{score}{money(s.total_price, cur)} total before taxes "
                    f"({money(s.price_per_night, cur)} per night, all rooms){cancel}"
                )
                if s.url:
                    st.markdown(f"[View on Booking.com]({s.url})")
        if not stays:
            st.write("No hotels available.")

    # ---- activities
    with tab_activities:
        st.caption("AI estimates. Check official booking sites before relying on these prices.")
        for a in activities:
            with st.container(border=True):
                st.markdown(f"**{a.name}**")
                st.write(a.description)
                st.caption(
                    f"{money(a.price_estimate, cur)} per person · about {a.duration_hours:g} h"
                )
        if not activities:
            st.write("No activities available.")

    # ---- itinerary
    with tab_plan:
        st.caption("Written by AI from the results above. Flight and activity details are estimates.")
        summary_text = state.get("summary")
        if summary_text:
            st.write(summary_text)
        else:
            st.write("No itinerary available.")
