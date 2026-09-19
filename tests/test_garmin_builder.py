import unittest

from garmin_builder import (
    build_executable_step,
    build_garmin_workout,
    build_repeat_group,
    build_workout_steps,
    count_required_step_ids,
)
from models import (
    DistanceUnit,
    EndType,
    RepeatBlock,
    Step,
    StepRole,
    Target,
    Workout,
)


class TestGarminBuilder(unittest.TestCase):

    def test_build_time_interval_without_target(self):
        step = Step(
            role=StepRole.INTERVAL,
            end_type=EndType.TIME,
            value=20,
        )

        result = build_executable_step(
            step=step,
            step_id=1001,
            step_order=1,
            child_step_id=1,
        )

        self.assertEqual(result["type"], "ExecutableStepDTO")
        self.assertEqual(
            result["stepType"]["stepTypeKey"],
            "interval",
        )
        self.assertEqual(
            result["endCondition"]["conditionTypeKey"],
            "time",
        )
        self.assertEqual(result["endConditionValue"], 20.0)
        self.assertIsNone(result["preferredEndConditionUnit"])
        self.assertEqual(
            result["targetType"]["workoutTargetTypeKey"],
            "no.target",
        )

    def test_build_distance_warmup_with_hr_range(self):
        step = Step(
            role=StepRole.WARMUP,
            end_type=EndType.DISTANCE,
            value=7500,
            target=Target.heart_rate(125, 138),
            preferred_unit=DistanceUnit.KILOMETER,
        )

        result = build_executable_step(
            step=step,
            step_id=1002,
            step_order=2,
        )

        self.assertEqual(
            result["stepType"]["stepTypeKey"],
            "warmup",
        )
        self.assertEqual(
            result["endCondition"]["conditionTypeKey"],
            "distance",
        )
        self.assertEqual(result["endConditionValue"], 7500.0)
        self.assertEqual(
            result["preferredEndConditionUnit"]["unitKey"],
            "kilometer",
        )
        self.assertEqual(
            result["targetType"]["workoutTargetTypeKey"],
            "heart.rate.zone",
        )
        self.assertEqual(result["targetValueOne"], 125.0)
        self.assertEqual(result["targetValueTwo"], 138.0)
        self.assertIsNone(result["zoneNumber"])

    def test_build_repeat_group(self):
        repeat_block = RepeatBlock(
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
        )

        result = build_repeat_group(
            repeat_block=repeat_block,
            step_id=2000,
            step_order=2,
            child_step_id=1,
            child_step_ids=[2001, 2002],
            child_step_orders=[3, 4],
        )

        self.assertEqual(result["type"], "RepeatGroupDTO")
        self.assertEqual(
            result["stepType"]["stepTypeKey"],
            "repeat",
        )
        self.assertEqual(result["numberOfIterations"], 6)
        self.assertEqual(result["endConditionValue"], 6.0)
        self.assertEqual(
            result["endCondition"]["conditionTypeKey"],
            "iterations",
        )
        self.assertFalse(result["skipLastRestStep"])
        self.assertFalse(result["smartRepeat"])
        self.assertEqual(len(result["workoutSteps"]), 2)

        recovery = result["workoutSteps"][1]
        self.assertEqual(
            recovery["preferredEndConditionUnit"]["unitKey"],
            "meter",
        )

    def _example_a(self):
        return Workout(
            name="Facile + allunghi",
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

    def test_count_required_step_ids_for_example_a(self):
        workout = self._example_a()
        self.assertEqual(count_required_step_ids(workout), 5)

    def test_build_workout_steps_assigns_validated_order_pattern(self):
        workout = self._example_a()

        steps = build_workout_steps(
            workout,
            step_ids=[
                14651347805,
                14651347806,
                14651347807,
                14651347808,
                14651347809,
            ],
        )

        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0]["stepOrder"], 1)
        self.assertEqual(steps[1]["stepOrder"], 2)
        self.assertEqual(steps[1]["workoutSteps"][0]["stepOrder"], 3)
        self.assertEqual(steps[1]["workoutSteps"][1]["stepOrder"], 4)
        self.assertEqual(steps[2]["stepOrder"], 5)

        self.assertEqual(
            steps[0]["preferredEndConditionUnit"]["unitKey"],
            "kilometer",
        )
        self.assertEqual(
            steps[1]["workoutSteps"][1]["preferredEndConditionUnit"]["unitKey"],
            "meter",
        )
        self.assertEqual(
            steps[2]["preferredEndConditionUnit"]["unitKey"],
            "meter",
        )

    def test_build_complete_garmin_workout_shape(self):
        workout = self._example_a()

        result = build_garmin_workout(
            workout,
            step_ids=[
                14651347805,
                14651347806,
                14651347807,
                14651347808,
                14651347809,
            ],
            description="Example A generated by tests",
        )

        self.assertIsNone(result["workoutId"])
        self.assertIsNone(result["ownerId"])
        self.assertEqual(result["workoutName"], "Facile + allunghi")
        self.assertEqual(
            result["sportType"]["sportTypeKey"],
            "running",
        )
        self.assertFalse(result["shared"])

        segment = result["workoutSegments"][0]
        self.assertEqual(len(segment["workoutSteps"]), 3)

        warmup = segment["workoutSteps"][0]
        repeat = segment["workoutSteps"][1]
        cooldown = segment["workoutSteps"][2]

        self.assertEqual(
            warmup["preferredEndConditionUnit"]["unitKey"],
            "kilometer",
        )
        self.assertEqual(repeat["numberOfIterations"], 6)
        self.assertEqual(
            cooldown["preferredEndConditionUnit"]["unitKey"],
            "meter",
        )

    def test_build_workout_rejects_wrong_number_of_step_ids(self):
        workout = self._example_a()

        with self.assertRaises(ValueError):
            build_garmin_workout(
                workout,
                step_ids=[1, 2],
            )


if __name__ == "__main__":
    unittest.main()
