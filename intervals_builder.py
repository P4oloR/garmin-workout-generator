from models import DistanceUnit, EndType, RepeatBlock, Step, StepRole, TargetKind, Workout


INTENSITY_BY_ROLE = {
    StepRole.WARMUP: "warmup",
    StepRole.INTERVAL: "interval",
    StepRole.RECOVERY: "recovery",
    StepRole.COOLDOWN: "cooldown",
}


def _format_number(value: float) -> str:
    value = float(value)
    return str(int(value)) if value.is_integer() else f"{value:g}"


def _format_duration(step: Step) -> str:
    if step.end_type == EndType.LAP_BUTTON:
        raise ValueError(
            "Intervals.icu export: LAP button is not yet validated."
        )

    if step.end_type == EndType.TIME:
        seconds = float(step.value)
        if seconds.is_integer() and int(seconds) % 60 == 0:
            return f"{int(seconds) // 60}m"
        return f"{_format_number(seconds)}s"

    if step.end_type == EndType.DISTANCE:
        meters = float(step.value)
        if step.preferred_unit == DistanceUnit.KILOMETER:
            return f"{_format_number(meters / 1000.0)}km"
        return f"{_format_number(meters)}m"

    raise ValueError(f"Unsupported end type: {step.end_type}")


def _format_pace(seconds_per_km: float) -> str:
    seconds = int(round(seconds_per_km))
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes}:{remainder:02d}"


def _format_target(step: Step) -> str:
    target = step.target

    if target.kind == TargetKind.NONE:
        return ""

    if target.kind == TargetKind.HEART_RATE_ZONE:
        return f" Z{target.zone_number} HR"

    if target.kind == TargetKind.HEART_RATE_RANGE:
        return f" {target.min_bpm}-{target.max_bpm} HR"

    if target.kind == TargetKind.PACE_RANGE:
        fast = _format_pace(target.pace_fast_seconds_per_km)
        slow = _format_pace(target.pace_slow_seconds_per_km)
        return f" {fast}-{slow} Pace"

    raise ValueError(f"Unsupported target kind: {target.kind}")


def _format_intensity(step: Step) -> str:
    intensity = INTENSITY_BY_ROLE.get(step.role)
    return f" intensity={intensity}" if intensity else ""


def build_intervals_step(step: Step) -> str:
    return (
        f"- {_format_duration(step)}"
        f"{_format_target(step)}"
        f"{_format_intensity(step)}"
    )


def build_intervals_workout(workout: Workout) -> str:
    lines = []

    for item in workout.steps:
        if isinstance(item, Step):
            lines.append(build_intervals_step(item))
            continue

        if isinstance(item, RepeatBlock):
            lines.append(f"{item.repetitions}x")
            lines.extend(build_intervals_step(step) for step in item.steps)
            continue

        raise TypeError(f"Unsupported workout item: {type(item)!r}")

    return "\n".join(lines)
