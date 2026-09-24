import unittest

from app import parse_pace
from garmin_builder import build_executable_step
from models import (
    DistanceUnit,
    EndType,
    Step,
    StepRole,
    Target,
)


class TestPaceTarget(unittest.TestCase):

    def test_parse_pace_mm_ss(self):
        self.assertEqual(parse_pace("4:10", "Passo"), 250.0)
        self.assertEqual(parse_pace("4:20", "Passo"), 260.0)

    def test_parse_pace_rejects_invalid_seconds(self):
        with self.assertRaises(ValueError):
            parse_pace("4:75", "Passo")

    def test_pace_target_requires_fast_bound_first(self):
        with self.assertRaises(ValueError):
            Target.pace_range(260, 250)

    def test_pace_target_converts_to_garmin_speed_values(self):
        step = Step(
            role=StepRole.INTERVAL,
            end_type=EndType.DISTANCE,
            value=2000,
            preferred_unit=DistanceUnit.KILOMETER,
            target=Target.pace_range(250, 260),
        )

        result = build_executable_step(
            step=step,
            step_id=None,
            step_order=1,
        )

        self.assertEqual(
            result["targetType"]["workoutTargetTypeId"],
            6,
        )
        self.assertEqual(
            result["targetType"]["workoutTargetTypeKey"],
            "pace.zone",
        )
        self.assertAlmostEqual(
            result["targetValueOne"],
            4.0,
            places=9,
        )
        self.assertAlmostEqual(
            result["targetValueTwo"],
            1000.0 / 260.0,
            places=9,
        )
        self.assertIsNone(result["targetValueUnit"])
        self.assertIsNone(result["zoneNumber"])

    def test_reference_pace_values_round_trip_to_expected_pace(self):
        reference_fast_mps = 3.6630037
        reference_slow_mps = 3.6101083

        fast_seconds = 1000.0 / reference_fast_mps
        slow_seconds = 1000.0 / reference_slow_mps

        self.assertAlmostEqual(fast_seconds, 273.0, delta=0.05)
        self.assertAlmostEqual(slow_seconds, 277.0, delta=0.05)


if __name__ == "__main__":
    unittest.main()
