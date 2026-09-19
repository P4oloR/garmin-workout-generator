import json
import unittest
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


REFERENCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "validated_easy_strides_hr_range.json"
)


def build_reference_equivalent_workout():
    return Workout(
        name="FAA2 Facile + allunghi - copy",
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


class TestValidatedReference(unittest.TestCase):

    def test_generated_structure_matches_validated_reference(self):
        reference = json.loads(
            REFERENCE_PATH.read_text(encoding="utf-8")
        )

        generated = build_garmin_workout(
            build_reference_equivalent_workout(),
            step_ids=[
                14651347805,
                14651347806,
                14651347807,
                14651347808,
                14651347809,
            ],
            description=reference["description"],
        )

        reference_steps = reference["workoutSegments"][0]["workoutSteps"]
        generated_steps = generated["workoutSegments"][0]["workoutSteps"]

        self.assertEqual(
            generated["sportType"],
            reference["sportType"],
        )
        self.assertEqual(
            generated["workoutSegments"][0]["sportType"],
            reference["workoutSegments"][0]["sportType"],
        )
        self.assertEqual(
            len(generated_steps),
            len(reference_steps),
        )

        # Warmup
        self.assertEqual(
            generated_steps[0]["type"],
            reference_steps[0]["type"],
        )
        self.assertEqual(
            generated_steps[0]["stepType"],
            reference_steps[0]["stepType"],
        )
        self.assertEqual(
            generated_steps[0]["endCondition"],
            reference_steps[0]["endCondition"],
        )
        self.assertEqual(
            generated_steps[0]["endConditionValue"],
            reference_steps[0]["endConditionValue"],
        )
        self.assertEqual(
            generated_steps[0]["preferredEndConditionUnit"],
            reference_steps[0]["preferredEndConditionUnit"],
        )
        self.assertEqual(
            generated_steps[0]["targetType"],
            reference_steps[0]["targetType"],
        )
        self.assertEqual(
            generated_steps[0]["targetValueOne"],
            reference_steps[0]["targetValueOne"],
        )
        self.assertEqual(
            generated_steps[0]["targetValueTwo"],
            reference_steps[0]["targetValueTwo"],
        )

        # Repeat group
        generated_repeat = generated_steps[1]
        reference_repeat = reference_steps[1]

        self.assertEqual(
            generated_repeat["type"],
            reference_repeat["type"],
        )
        self.assertEqual(
            generated_repeat["stepType"],
            reference_repeat["stepType"],
        )
        self.assertEqual(
            generated_repeat["numberOfIterations"],
            reference_repeat["numberOfIterations"],
        )
        self.assertEqual(
            generated_repeat["endCondition"],
            reference_repeat["endCondition"],
        )
        self.assertEqual(
            generated_repeat["skipLastRestStep"],
            reference_repeat["skipLastRestStep"],
        )
        self.assertEqual(
            generated_repeat["smartRepeat"],
            reference_repeat["smartRepeat"],
        )
        self.assertEqual(
            generated_repeat["workoutSteps"],
            reference_repeat["workoutSteps"],
        )

        # Cooldown
        self.assertEqual(
            generated_steps[2],
            reference_steps[2],
        )

    def test_known_root_differences_are_non_structural(self):
        reference = json.loads(
            REFERENCE_PATH.read_text(encoding="utf-8")
        )

        generated = build_garmin_workout(
            build_reference_equivalent_workout(),
            step_ids=[
                14651347805,
                14651347806,
                14651347807,
                14651347808,
                14651347809,
            ],
            description=reference["description"],
        )

        self.assertIsNone(generated["estimatedDurationInSecs"])
        self.assertIsNone(generated["estimatedDistanceInMeters"])
        self.assertIsNone(generated["avgTrainingSpeed"])
        self.assertIsNone(generated["estimateType"])
        self.assertIsNone(generated["estimatedDistanceUnit"])
        self.assertIsNone(generated["workoutThumbnailUrl"])

        self.assertIsNotNone(reference["estimatedDurationInSecs"])
        self.assertIsNotNone(reference["estimatedDistanceInMeters"])
        self.assertIsNotNone(reference["avgTrainingSpeed"])
        self.assertIsNotNone(reference["estimateType"])
        self.assertIsNotNone(reference["estimatedDistanceUnit"])
        self.assertIsNotNone(reference["workoutThumbnailUrl"])


if __name__ == "__main__":
    unittest.main()
