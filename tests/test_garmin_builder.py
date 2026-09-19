import unittest

from garmin_builder import build_executable_step
from models import EndType, Step, StepRole, Target


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
            value=2500,
            target=Target.heart_rate(125, 138),
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
        self.assertEqual(result["endConditionValue"], 2500.0)
        self.assertEqual(
            result["preferredEndConditionUnit"]["unitKey"],
            "meter",
        )
        self.assertEqual(
            result["targetType"]["workoutTargetTypeKey"],
            "heart.rate.zone",
        )
        self.assertEqual(result["targetValueOne"], 125.0)
        self.assertEqual(result["targetValueTwo"], 138.0)
        self.assertIsNone(result["zoneNumber"])


if __name__ == "__main__":
    unittest.main()
