import os
import unittest
from unittest.mock import Mock, patch

import app as app_module


POC8_PAYLOAD = {
    "name": "PoC8 GUI Test",
    "date": "2026-09-22",
    "items": [
        {
            "type": "step",
            "role": "warmup",
            "end_type": "distance",
            "value": 3,
            "unit": "km",
            "target": "none",
        },
        {
            "type": "repeat",
            "repetitions": 2,
            "work": {
                "end_type": "distance",
                "value": 1,
                "unit": "km",
                "target": "pace",
                "pace_fast": "4:28",
                "pace_slow": "4:32",
            },
            "recovery": {
                "end_type": "distance",
                "value": 1,
                "unit": "km",
                "target": "hr_zone",
                "zone": 1,
            },
        },
        {
            "type": "step",
            "role": "cooldown",
            "end_type": "distance",
            "value": 2,
            "unit": "km",
            "target": "none",
        },
    ],
}


class IntervalsEndpointTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config.update(TESTING=True)
        self.client = app_module.app.test_client()

    def test_missing_api_key_is_rejected_without_network_call(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
            app_module.requests, "post"
        ) as post:
            response = self.client.post("/send-to-intervals", json=POC8_PAYLOAD)

        self.assertEqual(response.status_code, 400)
        self.assertIn("INTERVALS_API_KEY", response.get_json()["error"])
        post.assert_not_called()

    def test_poc8_payload_sent_to_intervals(self):
        response_mock = Mock()
        response_mock.ok = True
        response_mock.json.return_value = [
            {
                "id": 123,
                "name": "PoC8 GUI Test",
                "start_date_local": "2026-09-22T00:00:00",
            }
        ]

        with patch.dict(
            os.environ, {"INTERVALS_API_KEY": "test-secret"}, clear=True
        ), patch.object(
            app_module.requests, "post", return_value=response_mock
        ) as post:
            response = self.client.post("/send-to-intervals", json=POC8_PAYLOAD)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])

        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["auth"], ("API_KEY", "test-secret"))
        self.assertEqual(kwargs["params"], {"upsert": "true"})
        self.assertEqual(
            kwargs["json"][0]["description"],
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
        self.assertEqual(
            kwargs["json"][0]["start_date_local"],
            "2026-09-22T00:00:00",
        )
        self.assertNotIn("test-secret", str(kwargs["json"]))

    def test_api_error_is_returned_as_bad_gateway(self):
        response_mock = Mock()
        response_mock.ok = False
        response_mock.status_code = 401
        response_mock.text = "Unauthorized"

        with patch.dict(
            os.environ, {"INTERVALS_API_KEY": "bad-secret"}, clear=True
        ), patch.object(
            app_module.requests, "post", return_value=response_mock
        ):
            response = self.client.post("/send-to-intervals", json=POC8_PAYLOAD)

        self.assertEqual(response.status_code, 502)
        self.assertIn("HTTP 401", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
