import unittest

from garmin_builder import build_executable_step
from models import EndType, Step, StepRole, Target


class TestLapButton(unittest.TestCase):

    def test_lap_button_step_without_target(self):
        step = Step(
            role=StepRole.OTHER,
            end_type=EndType.LAP_BUTTON,
            target=Target.none(),
        )
        result = build_executable_step(step, None, 1)
        self.assertEqual(result["stepType"]["stepTypeKey"], "other")
        self.assertEqual(result["endCondition"]["conditionTypeId"], 1)
        self.assertEqual(result["endCondition"]["conditionTypeKey"], "lap.button")
        self.assertEqual(result["endConditionValue"], 1000.0)
        self.assertIsNone(result["preferredEndConditionUnit"])
        self.assertEqual(result["targetType"]["workoutTargetTypeKey"], "no.target")

    def test_lap_button_can_have_hr_zone_target(self):
        step = Step(
            role=StepRole.OTHER,
            end_type=EndType.LAP_BUTTON,
            target=Target.heart_rate_zone(2),
        )
        result = build_executable_step(step, None, 1)
        self.assertEqual(result["endCondition"]["conditionTypeKey"], "lap.button")
        self.assertEqual(result["targetType"]["workoutTargetTypeKey"], "heart.rate.zone")
        self.assertEqual(result["zoneNumber"], 2)

    def test_lap_button_can_have_custom_hr_target(self):
        step = Step(
            role=StepRole.OTHER,
            end_type=EndType.LAP_BUTTON,
            target=Target.heart_rate(125, 138),
        )
        result = build_executable_step(step, None, 1)
        self.assertEqual(result["targetValueOne"], 125.0)
        self.assertEqual(result["targetValueTwo"], 138.0)

    def test_lap_button_rejects_user_value(self):
        with self.assertRaises(ValueError):
            Step(
                role=StepRole.OTHER,
                end_type=EndType.LAP_BUTTON,
                value=500,
            )


if __name__ == "__main__":
    unittest.main()
