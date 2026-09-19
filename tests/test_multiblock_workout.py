import unittest

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


class TestMultiBlockWorkout(unittest.TestCase):

    def test_multiple_single_and_repeat_blocks(self):
        workout = Workout(
            name="Multi block",
            steps=[
                Step(
                    role=StepRole.WARMUP,
                    end_type=EndType.DISTANCE,
                    value=2500,
                    preferred_unit=DistanceUnit.KILOMETER,
                    target=Target.heart_rate_zone(1),
                ),
                RepeatBlock(
                    repetitions=4,
                    steps=[
                        Step(
                            role=StepRole.INTERVAL,
                            end_type=EndType.DISTANCE,
                            value=100,
                        ),
                        Step(
                            role=StepRole.RECOVERY,
                            end_type=EndType.DISTANCE,
                            value=150,
                        ),
                    ],
                ),
                Step(
                    role=StepRole.INTERVAL,
                    end_type=EndType.DISTANCE,
                    value=500,
                    target=Target.heart_rate_zone(1),
                ),
                RepeatBlock(
                    repetitions=6,
                    steps=[
                        Step(
                            role=StepRole.INTERVAL,
                            end_type=EndType.DISTANCE,
                            value=800,
                            target=Target.heart_rate_zone(4),
                        ),
                        Step(
                            role=StepRole.RECOVERY,
                            end_type=EndType.DISTANCE,
                            value=300,
                            target=Target.heart_rate_zone(2),
                        ),
                    ],
                ),
                Step(
                    role=StepRole.COOLDOWN,
                    end_type=EndType.DISTANCE,
                    value=3000,
                    preferred_unit=DistanceUnit.KILOMETER,
                    target=Target.heart_rate_zone(2),
                ),
            ],
        )

        count = count_required_step_ids(workout)
        self.assertEqual(count, 9)

        result = build_garmin_workout(
            workout,
            step_ids=[None] * count,
        )

        steps = result["workoutSegments"][0]["workoutSteps"]

        self.assertEqual(len(steps), 5)
        self.assertEqual(steps[1]["type"], "RepeatGroupDTO")
        self.assertEqual(steps[3]["type"], "RepeatGroupDTO")
        self.assertEqual(steps[0]["zoneNumber"], 1)
        self.assertEqual(steps[3]["workoutSteps"][0]["zoneNumber"], 4)
        self.assertEqual(steps[3]["workoutSteps"][1]["zoneNumber"], 2)


if __name__ == "__main__":
    unittest.main()
