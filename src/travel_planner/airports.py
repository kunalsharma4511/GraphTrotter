"""City name -> IATA airport code. One main airport per city (a simplification)."""

CITY_TO_AIRPORT = {
    # India
    "indore": "IDR", "delhi": "DEL", "new delhi": "DEL", "mumbai": "BOM", "bangalore": "BLR",
    "bengaluru": "BLR", "hyderabad": "HYD", "chennai": "MAA", "kolkata": "CCU", "pune": "PNQ",
    "ahmedabad": "AMD", "goa": "GOI", "jaipur": "JAI", "bhopal": "BHO", "lucknow": "LKO",
    "kochi": "COK", "nagpur": "NAG", "chandigarh": "IXC",
    # International
    "london": "LHR", "paris": "CDG", "new york": "JFK", "dubai": "DXB", "singapore": "SIN",
    "bangkok": "BKK", "tokyo": "HND", "bali": "DPS", "kuala lumpur": "KUL", "hong kong": "HKG",
    "sydney": "SYD", "melbourne": "MEL", "toronto": "YYZ", "san francisco": "SFO",
    "los angeles": "LAX", "rome": "FCO", "amsterdam": "AMS", "frankfurt": "FRA", "zurich": "ZRH",
    "istanbul": "IST", "doha": "DOH", "abu dhabi": "AUH", "colombo": "CMB", "kathmandu": "KTM",
    "male": "MLE", "barcelona": "BCN", "madrid": "MAD", "berlin": "BER", "vienna": "VIE",
}


def resolve_airport(text: str | None) -> str | None:
    """'Indore' -> 'IDR', 'Paris, France' -> 'CDG', 'lhr' -> 'LHR', unknown -> None."""
    if not text:
        return None
    name = text.split(",")[0].strip().lower()
    if name in CITY_TO_AIRPORT:        # city names first, so "goa" is not read as a code
        return CITY_TO_AIRPORT[name]
    if len(name) == 3 and name.isalpha():
        return name.upper()            # the user typed an airport code directly
    return None