#!/usr/bin/env python3
"""Resolve Geoff's current working timezone from calendar context."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_TZ = "America/Los_Angeles"
CALENDAR_FILE = Path("/home/ubuntu/.openclaw/workspace/config/calendar-events.json")


@dataclass(frozen=True)
class TimezoneMatch:
    timezone_name: str
    label: str
    priority: int
    when: datetime | None = None
    in_transit: bool = False


OVERRIDE_FILE = Path("/home/ubuntu/.openclaw/workspace/state/user-location-override.json")
AERO_TRACKED_FLIGHTS_FILE = Path("/home/ubuntu/.openclaw/workspace/state/aero-tracked-flights.json")

AIRPORT_TIMEZONES = {
    "KLAX": "America/Los_Angeles",
    "LAX": "America/Los_Angeles",
    "KBUR": "America/Los_Angeles",
    "BUR": "America/Los_Angeles",
    "KVNY": "America/Los_Angeles",
    "VNY": "America/Los_Angeles",
    "KLGB": "America/Los_Angeles",
    "LGB": "America/Los_Angeles",
    "KONT": "America/Los_Angeles",
    "ONT": "America/Los_Angeles",
    "KSFO": "America/Los_Angeles",
    "SFO": "America/Los_Angeles",
    "KRNO": "America/Los_Angeles",
    "RNO": "America/Los_Angeles",
    "KPDX": "America/Los_Angeles",
    "PDX": "America/Los_Angeles",
    "KJFK": "America/New_York",
    "JFK": "America/New_York",
    "KLGA": "America/New_York",
    "LGA": "America/New_York",
    "KEWR": "America/New_York",
    "EWR": "America/New_York",
    "KPVD": "America/New_York",
    "PVD": "America/New_York",
    "KBOS": "America/New_York",
    "BOS": "America/New_York",
    "KATL": "America/New_York",
    "ATL": "America/New_York",
    "KORD": "America/Chicago",
    "ORD": "America/Chicago",
    "KDFW": "America/Chicago",
    "DFW": "America/Chicago",
    "KDEN": "America/Denver",
    "DEN": "America/Denver",
    "KSLC": "America/Denver",
    "SLC": "America/Denver",
    "KPHX": "America/Phoenix",
    "PHX": "America/Phoenix",
    "CYYZ": "America/Toronto",
    "YYZ": "America/Toronto",
}


ZONE_RULES = [
    ("America/Los_Angeles", ["los angeles", "lax", "burbank", "bur", "calabasas", "malibu", "santa monica", "venice", "san diego", "palm springs", "reno", "tahoe", "truckee", "san francisco", "sfo", "portland", "pdx"]),
    ("America/New_York", ["new york", "nyc", "jfk", "lga", "ewr", "providence", "pvd", "boston", "atlanta", "atl", "washington", "dc"]),
    ("America/Chicago", ["chicago", "ord", "austin", "dallas", "dfw"]),
    ("America/Denver", ["denver", "salt lake city", "slc"]),
    ("America/Phoenix", ["phoenix", "scottsdale", "phx"]),
    ("America/Toronto", ["toronto", "ontario", "niagara"]),
    ("Europe/London", ["london", "heathrow", "lgw"]),
    ("Europe/Paris", ["paris", "cdg"]),
]


def _load_events() -> list[dict]:
    try:
        data = json.loads(CALENDAR_FILE.read_text())
        return data.get("events", [])
    except Exception:
        return []


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _airport_timezone(code: str | None) -> str | None:
    if not code:
        return None
    normalized = code.upper()
    return AIRPORT_TIMEZONES.get(normalized) or AIRPORT_TIMEZONES.get(normalized.lstrip("K"))


def _override_match(now_utc: datetime) -> TimezoneMatch | None:
    try:
        data = json.loads(OVERRIDE_FILE.read_text())
    except Exception:
        return None

    timezone_name = data.get("timezone")
    if not timezone_name:
        return None

    expires_at = _parse_dt(data.get("expires_at"))
    if expires_at and now_utc >= expires_at:
        return None

    try:
        ZoneInfo(timezone_name)
    except Exception:
        return None

    label = data.get("label") or "manual location override"
    return TimezoneMatch(timezone_name, label, 200, expires_at)


def _aero_match(now_utc: datetime) -> TimezoneMatch | None:
    try:
        flights = json.loads(AERO_TRACKED_FLIGHTS_FILE.read_text())
    except Exception:
        return None

    matches: list[TimezoneMatch] = []
    for flight in flights.values():
        origin = flight.get("origin")
        destination = flight.get("destination")
        origin_tz = _airport_timezone(origin)
        destination_tz = _airport_timezone(destination)
        departure = _parse_dt(flight.get("estimated_departure")) or _parse_dt(flight.get("scheduled_departure"))
        arrival = _parse_dt(flight.get("estimated_arrival")) or _parse_dt(flight.get("scheduled_arrival"))
        flight_number = flight.get("flight_number", "flight")

        if departure and origin_tz and departure - timedelta(hours=6) <= now_utc < departure:
            matches.append(TimezoneMatch(origin_tz, f"aero pre-flight: {flight_number} from {origin}", 120, departure))

        if departure and arrival and destination_tz and departure <= now_utc <= arrival:
            matches.append(TimezoneMatch(destination_tz, f"aero in transit: {flight_number} to {destination}", 130, departure, True))

        if arrival and destination_tz and arrival < now_utc <= arrival + timedelta(hours=24):
            matches.append(TimezoneMatch(destination_tz, f"aero recent arrival: {flight_number} to {destination}", 125, arrival))

    if not matches:
        return None
    matches.sort(key=lambda m: (m.priority, m.when or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    return matches[0]


def _parse_start(event: dict) -> datetime | None:
    raw = event.get("start_raw")
    if not raw:
        return None
    try:
        if "T" in raw:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _zone_from_text(text: str) -> tuple[str, str] | None:
    lower = text.lower()
    for timezone_name, keywords in ZONE_RULES:
        for keyword in keywords:
            if keyword in lower:
                return timezone_name, keyword
    return None


def _event_match(event: dict, now_utc: datetime) -> TimezoneMatch | None:
    start = _parse_start(event)
    if start is None:
        return None

    text = " ".join([
        event.get("summary", ""),
        event.get("location", ""),
        event.get("description", ""),
    ])
    summary = event.get("summary", "calendar event")
    location = event.get("location", "")
    lower_summary = summary.lower()

    # For route strings like "Los Angeles(LAX) - Atlanta(ATL)", use the
    # departure side before takeoff and the arrival side after takeoff.
    if any(word in lower_summary for word in ["flight", "delta", "united", "american"]) and "-" in location and "T" in str(event.get("start_raw", "")):
        origin_text, destination_text = location.split("-", 1)
        origin_zone = _zone_from_text(origin_text)
        destination_zone = _zone_from_text(destination_text)
        if origin_zone and start - timedelta(hours=6) <= now_utc < start:
            return TimezoneMatch(origin_zone[0], f"calendar pre-flight: {origin_zone[1]}", 95, start)
        if destination_zone and start <= now_utc <= start + timedelta(hours=18):
            return TimezoneMatch(destination_zone[0], f"calendar flight destination: {destination_zone[1]}", 96, start, True)

    zone = _zone_from_text(text)
    if not zone:
        return None

    timezone_name, keyword = zone

    if "T" not in str(event.get("start_raw", "")):
        # All-day stay/trip events are strong location signals for several days.
        end = start + timedelta(days=5)
        if start.date() <= now_utc.date() <= end.date():
            return TimezoneMatch(timezone_name, f"calendar stay/trip: {keyword}", 90, start)
        return None

    # A recent flight arrival or travel event is the strongest transient signal.
    if any(word in lower_summary for word in ["flight", "delta", "united", "american"]):
        if start - timedelta(hours=2) <= now_utc <= start + timedelta(hours=18):
            return TimezoneMatch(timezone_name, f"recent travel: {keyword}", 100, start)

    # Same-day local events are useful when traveling.
    event_local_date = now_utc.astimezone(ZoneInfo(timezone_name)).date()
    start_local_date = start.astimezone(ZoneInfo(timezone_name)).date()
    if start_local_date == event_local_date:
        return TimezoneMatch(timezone_name, f"today's calendar: {keyword}", 70, start)

    return None


def resolve_timezone(now_utc: datetime | None = None) -> TimezoneMatch:
    now_utc = now_utc or datetime.now(timezone.utc)
    override = _override_match(now_utc)
    if override:
        return override
    aero = _aero_match(now_utc)
    if aero:
        return aero
    matches = [
        match
        for event in _load_events()
        if (match := _event_match(event, now_utc)) is not None
    ]
    if not matches:
        return TimezoneMatch(DEFAULT_TZ, "default home timezone", 0, None)
    matches.sort(key=lambda m: (m.priority, m.when or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    return matches[0]


def local_now(now_utc: datetime | None = None) -> datetime:
    match = resolve_timezone(now_utc)
    return (now_utc or datetime.now(timezone.utc)).astimezone(ZoneInfo(match.timezone_name))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--field", choices=["timezone", "datetime", "date", "hm", "label", "shell"], default="datetime")
    args = parser.parse_args()

    now_utc = datetime.now(timezone.utc)
    match = resolve_timezone(now_utc)
    local = now_utc.astimezone(ZoneInfo(match.timezone_name))

    if args.field == "timezone":
        print(match.timezone_name)
    elif args.field == "date":
        print(local.strftime("%Y-%m-%d"))
    elif args.field == "hm":
        print(local.strftime("%H:%M"))
    elif args.field == "label":
        print(match.label)
    elif args.field == "shell":
        print(f"TZ_NAME={match.timezone_name}")
        print(f"LOCAL_DATE={local.strftime('%Y-%m-%d')}")
        print(f"LOCAL_TIME={local.strftime('%H:%M')}")
        print(f"LOCAL_ABBR={local.tzname()}")
        print(f"TZ_REASON={match.label}")
        print(f"IN_TRANSIT={'1' if match.in_transit else '0'}")
    else:
        print(local.isoformat())


if __name__ == "__main__":
    main()
