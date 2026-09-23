import io
import json
import os
import re
import sys

from flask import Flask, render_template, request, send_file, send_from_directory
import requests

from garmin_builder import build_garmin_workout, count_required_step_ids
from intervals_builder import build_intervals_workout
from models import (
    DistanceUnit,
    EndType,
    RepeatBlock,
    Step,
    StepRole,
    Target,
    Workout,
)


def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))

    return os.path.join(base_path, relative_path)


app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=None,
)


@app.get("/static/<path:filename>", endpoint="static")
def static_files(filename):
    return send_from_directory(
        resource_path("static"),
        filename,
    )


ROLE_MAP = {
    "warmup": StepRole.WARMUP,
    "run": StepRole.INTERVAL,
    "interval": StepRole.INTERVAL,
    "recovery": StepRole.RECOVERY,
    "cooldown": StepRole.COOLDOWN,
    "other": StepRole.OTHER,
}


def positive_float(value, label):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: valore non valido.") from exc

    if number <= 0:
        raise ValueError(f"{label}: deve essere maggiore di zero.")

    return number


def positive_int(value, label):
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: valore non valido.") from exc

    if number <= 0:
        raise ValueError(f"{label}: deve essere maggiore di zero.")

    return number


def parse_pace(value, label):
    if not isinstance(value, str):
        raise ValueError(f"{label}: usa il formato mm:ss.")

    text = value.strip()
    parts = text.split(":")

    if len(parts) != 2:
        raise ValueError(f"{label}: usa il formato mm:ss.")

    try:
        minutes = int(parts[0])
        seconds = int(parts[1])
    except ValueError as exc:
        raise ValueError(f"{label}: usa il formato mm:ss.") from exc

    if minutes < 0 or seconds < 0 or seconds > 59:
        raise ValueError(f"{label}: valore non valido.")

    total_seconds = minutes * 60 + seconds

    if total_seconds <= 0:
        raise ValueError(f"{label}: deve essere maggiore di zero.")

    return float(total_seconds)


def parse_target(data):
    kind = data.get("target", "none")

    if kind == "none":
        return Target.none()

    if kind == "hr_range":
        return Target.heart_rate(
            positive_int(data.get("hr_min"), "FC minima"),
            positive_int(data.get("hr_max"), "FC massima"),
        )

    if kind == "hr_zone":
        return Target.heart_rate_zone(
            positive_int(data.get("zone"), "Zona FC")
        )

    if kind == "pace":
        return Target.pace_range(
            parse_pace(
                data.get("pace_fast"),
                "Passo veloce",
            ),
            parse_pace(
                data.get("pace_slow"),
                "Passo lento",
            ),
        )

    raise ValueError("Target non supportato.")


def parse_step(data, default_role="run"):
    role_key = data.get("role", default_role)

    if role_key not in ROLE_MAP:
        raise ValueError("Tipo fase non supportato.")

    role = ROLE_MAP[role_key]
    end_type = data.get("end_type")

    if end_type == "distance":
        raw = positive_float(data.get("value"), "Distanza")
        unit = data.get("unit")

        if unit == "km":
            value = raw * 1000.0
            preferred_unit = DistanceUnit.KILOMETER
        elif unit == "m":
            value = raw
            preferred_unit = DistanceUnit.METER
        else:
            raise ValueError("Unità distanza non supportata.")

        return Step(
            role=role,
            end_type=EndType.DISTANCE,
            value=value,
            target=parse_target(data),
            preferred_unit=preferred_unit,
        )

    if end_type == "time":
        raw = positive_float(data.get("value"), "Tempo")
        unit = data.get("unit")

        if unit == "min":
            value = raw * 60.0
        elif unit == "s":
            value = raw
        else:
            raise ValueError("Unità tempo non supportata.")

        return Step(
            role=role,
            end_type=EndType.TIME,
            value=value,
            target=parse_target(data),
        )

    if end_type == "lap_button":
        return Step(
            role=role,
            end_type=EndType.LAP_BUTTON,
            value=None,
            target=parse_target(data),
        )

    raise ValueError("Tipo terminazione non supportato.")


def build_workout_from_payload(payload):
    name = (payload.get("name") or "").strip()

    if not name:
        raise ValueError("Inserisci il nome dell'allenamento.")

    raw_items = payload.get("items")

    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("Aggiungi almeno un blocco all'allenamento.")

    items = []

    for raw_item in raw_items:
        item_type = raw_item.get("type")

        if item_type == "step":
            items.append(parse_step(raw_item))

        elif item_type == "repeat":
            repetitions = positive_int(
                raw_item.get("repetitions"),
                "Ripetizioni",
            )

            work = parse_step(
                {
                    **raw_item.get("work", {}),
                    "role": "interval",
                }
            )

            recovery = parse_step(
                {
                    **raw_item.get("recovery", {}),
                    "role": "recovery",
                }
            )

            items.append(
                RepeatBlock(
                    repetitions=repetitions,
                    steps=[work, recovery],
                )
            )

        else:
            raise ValueError("Tipo blocco non supportato.")

    return Workout(name=name, steps=items)


INTERVALS_BASE_URL = "https://intervals.icu/api/v1"
WOL_BASE_URL = os.getenv(
    "WOL_BASE_URL",
    "https://workoutlink.paolo-ricciotti.workers.dev",
).rstrip("/")


def create_or_update_intervals_workout(api_key, workout, date_str):
    description = build_intervals_workout(workout)
    payload = [{
        "category": "WORKOUT",
        "start_date_local": f"{date_str}T00:00:00",
        "type": "Run",
        "name": workout.name,
        "description": description,
        "external_id": f"garmin-workout-generator-{date_str}-{safe_filename(workout.name)}",
    }]

    response = requests.post(
        f"{INTERVALS_BASE_URL}/athlete/0/events/bulk",
        params={"upsert": "true"},
        auth=("API_KEY", api_key),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "GarminWorkoutGenerator/0.1",
        },
        json=payload,
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Intervals.icu ha risposto HTTP {response.status_code}: {response.text}"
        )

    data = response.json()
    if not isinstance(data, list):
        raise RuntimeError(
            "Risposta inattesa da Intervals.icu: attesa una lista di eventi."
        )

    return data


def serialize_target_snapshot(target):
    return {
        "kind": target.kind.value,
        "min_bpm": target.min_bpm,
        "max_bpm": target.max_bpm,
        "zone_number": target.zone_number,
        "pace_fast_seconds_per_km": target.pace_fast_seconds_per_km,
        "pace_slow_seconds_per_km": target.pace_slow_seconds_per_km,
    }


def serialize_step_snapshot(step):
    return {
        "role": step.role.value,
        "end_type": step.end_type.value,
        "value": step.value,
        "preferred_unit": (
            step.preferred_unit.value
            if step.preferred_unit is not None
            else None
        ),
        "target": serialize_target_snapshot(step.target),
    }


def serialize_workout_snapshot(workout):
    serialized_steps = []

    for item in workout.steps:
        if isinstance(item, Step):
            serialized_steps.append(serialize_step_snapshot(item))
        elif isinstance(item, RepeatBlock):
            serialized_steps.append(
                {
                    "repetitions": item.repetitions,
                    "steps": [
                        serialize_step_snapshot(step)
                        for step in item.steps
                    ],
                }
            )
        else:
            raise TypeError(
                f"Tipo workout non supportato: {type(item)!r}"
            )

    return {
        "name": workout.name,
        "steps": serialized_steps,
    }


def safe_filename(name):
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    cleaned = cleaned.strip("._")
    return cleaned or "garmin_workout"


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/generate")
def generate():
    try:
        payload = request.get_json(force=True)
        workout = build_workout_from_payload(payload)

        step_ids = [None] * count_required_step_ids(workout)

        result = build_garmin_workout(
            workout=workout,
            step_ids=step_ids,
            description=None,
        )

        content = json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        ) + "\n"

        buffer = io.BytesIO(content.encode("utf-8"))
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype="application/json",
            as_attachment=True,
            download_name=f"{safe_filename(workout.name)}.json",
        )

    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return {
            "error": str(exc),
        }, 400


@app.post("/publish-to-wol")
def publish_to_wol():
    try:
        payload = request.get_json(force=True)

        title = (payload.get("title") or "").strip()
        if not title:
            raise ValueError("Inserisci il titolo della settimana.")

        raw_items = payload.get("items")
        if not isinstance(raw_items, list) or not raw_items:
            raise ValueError(
                "Aggiungi almeno un allenamento alla settimana."
            )

        if len(raw_items) > 7:
            raise ValueError(
                "La settimana può contenere al massimo 7 allenamenti."
            )

        publisher_key = os.getenv("WOL_PUBLISHER_KEY")
        if not publisher_key:
            raise ValueError(
                "Variabile WOL_PUBLISHER_KEY non impostata sul PC."
            )

        wol_items = []
        for index, raw_item in enumerate(raw_items):
            try:
                day_offset = int(raw_item.get("day_offset"))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Allenamento {index + 1}: giorno non valido."
                ) from exc

            if day_offset < 0 or day_offset > 6:
                raise ValueError(
                    f"Allenamento {index + 1}: giorno non valido."
                )

            raw_workout = raw_item.get("workout")
            if not isinstance(raw_workout, dict):
                raise ValueError(
                    f"Allenamento {index + 1}: dati workout mancanti."
                )

            workout = build_workout_from_payload(raw_workout)
            wol_items.append(
                {
                    "day_offset": day_offset,
                    "workout": serialize_workout_snapshot(workout),
                }
            )

        response = requests.post(
            f"{WOL_BASE_URL}/api/publish/plan",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {publisher_key}",
                "User-Agent": "WorkOutGenerator/0.1",
            },
            json={
                "title": title,
                "description": (
                    (payload.get("description") or "").strip() or None
                ),
                "items": wol_items,
            },
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                "WorkOutLink ha risposto "
                f"HTTP {response.status_code}: {response.text}"
            )

        data = response.json()
        if not isinstance(data, dict) or not data.get("url"):
            raise RuntimeError(
                "Risposta inattesa da WorkOutLink."
            )

        return {
            "ok": True,
            "message": "Settimana pubblicata su WorkOutLink.",
            "public_id": data.get("public_id"),
            "url": data["url"],
        }

    except requests.RequestException as exc:
        return {"error": f"Errore di rete verso WorkOutLink: {exc}"}, 502
    except RuntimeError as exc:
        return {"error": str(exc)}, 502
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return {"error": str(exc)}, 400


@app.post("/send-to-intervals")
def send_to_intervals():
    try:
        payload = request.get_json(force=True)
        workout = build_workout_from_payload(payload)

        date_str = (payload.get("date") or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
            raise ValueError("Inserisci una data valida nel formato YYYY-MM-DD.")

        api_key = os.getenv("INTERVALS_API_KEY")
        if not api_key:
            raise ValueError(
                "Variabile INTERVALS_API_KEY non impostata sul PC."
            )

        events = create_or_update_intervals_workout(
            api_key=api_key,
            workout=workout,
            date_str=date_str,
        )

        return {
            "ok": True,
            "message": "Workout inviato a Intervals.icu.",
            "events": events,
        }

    except requests.RequestException as exc:
        return {"error": f"Errore di rete: {exc}"}, 502
    except RuntimeError as exc:
        return {"error": str(exc)}, 502
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return {"error": str(exc)}, 400


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8780,
        debug=False,
    )
