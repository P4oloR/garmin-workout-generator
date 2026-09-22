import unittest

from intervals_builder import build_intervals_workout
from models import DistanceUnit, EndType, RepeatBlock, Step, StepRole, Target, Workout


class IntervalsBuilderTests(unittest.TestCase):
    def test_poc8_workout(self):
        workout = Workout(
            name="GWG PoC 8",
            steps=[
                Step(
                    role=StepRole.WARMUP,
                    end_type=EndType.DISTANCE,
                    value=3000,
                    target=Target.none(),
                    preferred_unit=DistanceUnit.KILOMETER,
                ),
                RepeatBlock(
                    repetitions=2,
                    steps=[
                        Step(
                            role=StepRole.INTERVAL,
                            end_type=EndType.DISTANCE,
                            value=1000,
                            target=Target.pace_range(268, 272),
                            preferred_unit=DistanceUnit.KILOMETER,
                        ),
                        Step(
                            role=StepRole.RECOVERY,
                            end_type=EndType.DISTANCE,
                            value=1000,
                            target=Target.heart_rate_zone(1),
                            preferred_unit=DistanceUnit.KILOMETER,
                        ),
                    ],
                ),
                Step(
                    role=StepRole.COOLDOWN,
                    end_type=EndType.DISTANCE,
                    value=2000,
                    target=Target.none(),
                    preferred_unit=DistanceUnit.KILOMETER,
                ),
            ],
        )

        self.assertEqual(
            build_intervals_workout(workout),
            "\n".join(
                [
                    "- 3km intensity=warmup",
                    "2x",
                    "- 1km 4:28-4:32 Pace intensity=interval",
                    "- 1km Z1 HR intensity=recovery",
                    "- 2km intensity=cooldown",
                ]
            ),
        )

    def test_time_units(self):
        workout = Workout(
            name="Time",
            steps=[
                Step(
                    role=StepRole.INTERVAL,
                    end_type=EndType.TIME,
                    value=60,
                    target=Target.none(),
                ),
                Step(
                    role=StepRole.RECOVERY,
                    end_type=EndType.TIME,
                    value=20,
                    target=Target.none(),
                ),
            ],
        )
        self.assertEqual(
            build_intervals_workout(workout),
            "- 1m intensity=interval\n- 20s intensity=recovery",
        )

    def test_lap_is_rejected_until_validated(self):
        workout = Workout(
            name="Lap",
            steps=[
                Step(
                    role=StepRole.OTHER,
                    end_type=EndType.LAP_BUTTON,
                    target=Target.none(),
                )
            ],
        )
        with self.assertRaisesRegex(ValueError, "not yet validated"):
            build_intervals_workout(workout)


if __name__ == "__main__":
    unittest.main()
