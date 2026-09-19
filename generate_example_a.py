import json
from pathlib import Path

from garmin_builder import build_garmin_workout
from models import (
    DistanceUnit,
    EndType,
    RepeatBlock,
    Step,
    StepRole,
    Target,
    Workout,
)


def build_example_a():
    return Workout(
        name="FAA2 Facile + allunghi - generated",
        steps=[
            Step(
                role=StepRole.WARMUP,
                end_type=EndType.DISTANCE,
                value=7500,
                target=Target.heart_rate(125, 138),
                preferred_unit=DistanceUnit.KILOMETER,
            ),
            RepeatBlock(
                repetitions=6,
                steps=[
                    Step(
                        role=StepRole.INTERVAL,
                        end_type=EndType.TIME,
                        value=20,
                    ),
                    Step(
                        role=StepRole.RECOVERY,
                        end_type=EndType.DISTANCE,
                        value=150,
                        preferred_unit=DistanceUnit.METER,
                    ),
                ],
            ),
            Step(
                role=StepRole.COOLDOWN,
                end_type=EndType.DISTANCE,
                value=1000,
                target=Target.heart_rate(125, 138),
                preferred_unit=DistanceUnit.METER,
            ),
        ],
    )


def main():
    workout = build_example_a()

    step_ids = [
        14651347805,
        14651347806,
        14651347807,
        14651347808,
        14651347809,
    ]

    garmin_workout = build_garmin_workout(
        workout,
        step_ids=step_ids,
        description=(
            "7.5 km facili FC 125-138 bpm; "
            "6 x (20s allungo + 150m recupero); "
            "1.0 km facili finali."
        ),
    )

    output_dir = Path("examples") / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "example_a_experimental.json"

    with output_path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(
            garmin_workout,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()
