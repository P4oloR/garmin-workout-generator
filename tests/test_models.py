import unittest

from models import (
    DistanceUnit,
    EndType,
    RepeatBlock,
    Step,
    StepRole,
    Target,
    Workout,
)


class TestWorkoutModels(unittest.TestCase):

    def test_example_a_can_be_represented(self):
        workout = Workout(
            name="Facile + allunghi",
            steps=[
                Step(
                    role=StepRole.WARMUP,
                    end_type=EndType.DISTANCE,
                    value=2500,
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
                        ),
                    ],
                ),
                Step(
                    role=StepRole.COOLDOWN,
                    end_type=EndType.DISTANCE,
                    value=1000,
                    target=Target.heart_rate(125, 138),
                ),
            ],
        )

        self.assertEqual(workout.name, "Facile + allunghi")
        self.assertEqual(len(workout.steps), 3)
        self.assertEqual(
            workout.steps[0].preferred_unit,
            DistanceUnit.KILOMETER,
        )

        repeat = workout.steps[1]

        self.assertEqual(repeat.repetitions, 6)
        self.assertEqual(len(repeat.steps), 2)

    def test_invalid_heart_rate_range_is_rejected(self):
        with self.assertRaises(ValueError):
            Target.heart_rate(140, 130)

    def test_repeat_block_requires_at_least_one_step(self):
        with self.assertRaises(ValueError):
            RepeatBlock(
                repetitions=3,
                steps=[],
            )

    def test_distance_defaults_to_meter(self):
        step = Step(
            role=StepRole.RECOVERY,
            end_type=EndType.DISTANCE,
            value=150,
        )

        self.assertEqual(
            step.preferred_unit,
            DistanceUnit.METER,
        )

    def test_time_step_rejects_distance_unit(self):
        with self.assertRaises(ValueError):
            Step(
                role=StepRole.INTERVAL,
                end_type=EndType.TIME,
                value=20,
                preferred_unit=DistanceUnit.KILOMETER,
            )


if __name__ == "__main__":
    unittest.main()
