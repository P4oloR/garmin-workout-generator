#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any

import requests

BASE_URL = "https://intervals.icu/api/v1"
DEFAULT_WORKOUT_NAME = "GWG PoC 2 - semantic steps"
EXTERNAL_ID_PREFIX = "garmin-workout-generator-poc2"

def build_workout_description() -> str:
    return """Warmup
- 5m intensity=warmup

2x
- 1m intensity=interval
- 2m intensity=recovery

Cooldown
- 5m intensity=cooldown"""

def build_payload(date_str: str) -> list[dict[str, Any]]:
    return [{
        "category": "WORKOUT",
        "start_date_local": f"{date_str}T00:00:00",
        "type": "Run",
        "name": DEFAULT_WORKOUT_NAME,
        "description": build_workout_description(),
        "external_id": f"{EXTERNAL_ID_PREFIX}-{date_str}",
    }]

def create_or_update_workout(api_key: str, date_str: str) -> list[dict[str, Any]]:
    r = requests.post(
        f"{BASE_URL}/athlete/0/events/bulk",
        params={"upsert": "true"},
        auth=("API_KEY", api_key),
        headers={"Accept":"application/json","Content-Type":"application/json"},
        json=build_payload(date_str),
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"HTTP {r.status_code}:\n{r.text}")
    data = r.json()
    if not isinstance(data, list):
        raise RuntimeError("Risposta inattesa: attesa una lista di eventi.")
    return data

def validate_date(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Formato data richiesto: YYYY-MM-DD") from exc
    return value

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, type=validate_date)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if args.dry_run:
        print(json.dumps(build_payload(args.date), indent=2, ensure_ascii=False))
        return 0

    api_key = os.getenv("INTERVALS_API_KEY")
    if not api_key:
        print("ERRORE: INTERVALS_API_KEY non impostata.", file=sys.stderr)
        return 2

    try:
        events = create_or_update_workout(api_key, args.date)
    except Exception as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 3

    print("Workout PoC 2 creato/aggiornato con successo.")
    for event in events:
        print(json.dumps({
            "id": event.get("id"),
            "name": event.get("name"),
            "date": event.get("start_date_local"),
            "workout_doc": event.get("workout_doc"),
        }, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
