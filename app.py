import io
import json
import os
import re
import sys

from flask import Flask, render_template, request, send_file, send_from_directory

from garmin_builder import build_garmin_workout, count_required_step_ids
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


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8780,
        debug=False,
    )
