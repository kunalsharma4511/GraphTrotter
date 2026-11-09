"""Faithfulness check: does an itinerary contain only facts that were in the data?"""
import re
from dataclasses import dataclass, field

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
_DATE_RE = re.compile(rf"\b(\d{{1,2}})\s+({'|'.join(MONTHS)})\b", re.I)
_ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_TIME_RE = re.compile(r"\b(\d{1,2}):(\d{2})\b")
_DAY_RE = re.compile(r"\bDay\s+\d+\b", re.I)
_NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
_NAME_RE = re.compile(r"[A-Z][A-Za-z'’\-]+(?:\s+[A-Z][A-Za-z'’\-]+)*")

# Generic words that start sentences or labels; they are not "names" to verify.
STOP_WORDS = {
    "mon", "tue", "wed", "thu", "fri", "sat", "sun", *MONTHS,
    "day", "arrive", "arrival", "depart", "departure", "check", "check-in", "check-out",
    "checkout", "free", "morning", "afternoon", "evening", "night", "full", "transfer",
    "settle", "enjoy", "explore", "visit", "return", "travel", "leisure", "relax",
    "remaining", "no", "rest", "optional", "flight", "hotel", "time", "spend", "head",
    "take", "walk", "stroll", "wander", "then", "the", "a", "an", "in", "on", "at", "to",
    "from", "with", "for", "after", "before", "of",
}


@dataclass
class FaithfulnessReport:
    numbers: list[str] = field(default_factory=list)   # in the itinerary, not in the facts
    times: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    names: list[str] = field(default_factory=list)     # soft: possible invented names
    checked: int = 0                                   # how many numbers, times and dates were checked

    @property
    def hard_failures(self) -> list[str]:
        return self.numbers + self.times + self.dates

    @property
    def passed(self) -> bool:
        return not self.hard_failures

    @property
    def score(self) -> float:
        if self.checked == 0:
            return 1.0
        return 1 - len(self.hard_failures) / self.checked


def _norm_num(token: str) -> str | None:
    token = token.replace(",", "").rstrip(".")
    try:
        return f"{float(token):.10g}"
    except ValueError:
        return None


def _strip_structure(text: str) -> str:
    """Remove day labels, ISO dates, times and dates, so only 'real' numbers remain."""
    for pattern in (_DAY_RE, _ISO_RE, _TIME_RE, _DATE_RE):
        text = pattern.sub(" ", text)
    return text


def _numbers(text: str) -> set[str]:
    found = (_norm_num(t) for t in _NUM_RE.findall(_strip_structure(text)))
    return {n for n in found if n is not None}


def _times(text: str) -> set[tuple[int, str]]:
    return {(int(h), m) for h, m in _TIME_RE.findall(text)}


def _dates(text: str) -> set[tuple[int, str]]:
    found = {(int(d), m.lower()) for d, m in _DATE_RE.findall(text)}
    for _year, month, day in _ISO_RE.findall(text):
        if 1 <= int(month) <= 12:
            found.add((int(day), MONTHS[int(month) - 1]))
    return found


def _unsupported_names(itinerary: str, facts_lower: str) -> list[str]:
    unsupported: list[str] = []
    for run in _NAME_RE.findall(itinerary):
        tokens = [t for t in run.split() if t.lower().strip("-'’") not in STOP_WORDS]
        if not tokens:
            continue
        candidate = " ".join(tokens)
        if candidate.lower() not in facts_lower and candidate not in unsupported:
            unsupported.append(candidate)
    return unsupported


def check_itinerary(itinerary: str, facts: str) -> FaithfulnessReport:
    """Compare every checkable claim in the itinerary with the facts it was written from."""
    i_numbers, i_times, i_dates = _numbers(itinerary), _times(itinerary), _dates(itinerary)
    report = FaithfulnessReport()
    report.checked = len(i_numbers) + len(i_times) + len(i_dates)
    report.numbers = sorted(i_numbers - _numbers(facts))
    report.times = [f"{h:02d}:{m}" for h, m in sorted(i_times - _times(facts))]
    report.dates = [f"{d:02d} {m.title()}" for d, m in sorted(i_dates - _dates(facts))]
    report.names = _unsupported_names(itinerary, facts.lower())
    return report