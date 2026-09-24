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
WORKOUT_NAME = "GWG PoC 6 - Pace absolute"
EXTERNAL_ID_PREFIX = "garmin-workout-generator-poc6"

def build_workout_description() -> str:
    return """Warmup
- 5m 6:00/km Pace intensity=warmup

2x
- 1m 4:30/km Pace intensity=interval
- 2m 6:00/km Pace intensity=recovery

Cooldown
- 5m 6:00/km Pace intensity=cooldown"""

def build_payload(date_str: str) -> list[dict[str, Any]]:
    return [{
        "category": "WORKOUT",
        "start_date_local": f"{date_str}T00:00:00",
        "type": "Run",
        "name": WORKOUT_NAME,
        "description": build_workout_description(),
        "external_id": f"{EXTERNAL_ID_PREFIX}-{date_str}",
    }]

def create_or_update_workout(api_key: str, date_str: str) -> list[dict[str, Any]]:
    response = requests.post(
        f"{BASE_URL}/athlete/0/events/bulk",
        params={"upsert": "true"},
        auth=("API_KEY", api_key),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "GarminWorkoutGenerator-PoC/0.5",
        },
        json=build_payload(date_str),
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Intervals.icu ha risposto HTTP {response.status_code}:\n"
            f"{response.text}"
        )

    data = response.json()
    if not isinstance(data, list):
        raise RuntimeError(
            "Risposta inattesa da Intervals.icu: attesa una lista di eventi."
        )

    return data

def validate_date(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "La data deve essere nel formato YYYY-MM-DD, es. 2026-09-26."
        ) from exc

    return value

def main() -> int:
    parser = argparse.ArgumentParser(
        description="PoC 6: verifica target passo assoluto via Intervals.icu -> Garmin."
    )
    parser.add_argument(
        "--date",
        required=True,
        type=validate_date,
        help="Data del workout, formato YYYY-MM-DD.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra il payload senza inviarlo a Intervals.icu.",
    )
    args = parser.parse_args()

    payload = build_payload(args.date)

    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    api_key = os.getenv("INTERVALS_API_KEY")
    if not api_key:
        print(
            "ERRORE: variabile INTERVALS_API_KEY non impostata.\n"
            '$env:INTERVALS_API_KEY="la_tua_chiave"',
            file=sys.stderr,
        )
        return 2

    try:
        events = create_or_update_workout(api_key, args.date)
    except requests.RequestException as exc:
        print(f"ERRORE di rete: {exc}", file=sys.stderr)
        return 3
    except RuntimeError as exc:
        print(f"ERRORE API: {exc}", file=sys.stderr)
        return 4

    print("Workout PoC 6 creato/aggiornato con successo.")

    for event in events:
        print(
            json.dumps(
                {
                    "id": event.get("id"),
                    "name": event.get("name"),
                    "date": event.get("start_date_local"),
                    "category": event.get("category"),
                    "type": event.get("type"),
                    "external_id": event.get("external_id"),
                    "workout_doc": event.get("workout_doc"),
                },
                indent=2,
                ensure_ascii=False,
            )
        )

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
