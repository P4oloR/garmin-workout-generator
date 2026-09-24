import os
import unittest
from unittest.mock import Mock, patch

import app as app_module


WEEK_PAYLOAD = {
    "title": "Settimana Test",
    "description": "PoC WOG -> WOL",
    "items": [
        {
            "day_offset": 1,
            "workout": {
                "name": "Facile",
                "items": [
                    {
                        "type": "step",
                        "role": "warmup",
                        "end_type": "distance",
                        "value": 3,
                        "unit": "km",
                        "target": "none",
                    }
                ],
            },
        },
        {
            "day_offset": 3,
            "workout": {
                "name": "Soglia",
                "items": [
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
                    }
                ],
            },
        },
    ],
}


class WolPublishEndpointTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config.update(TESTING=True)
        self.client = app_module.app.test_client()

    def test_missing_publisher_key_is_rejected_without_network_call(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
            app_module,
            "get_wol_creator_token",
            return_value=None,
        ), patch.object(
            app_module,
            "get_wol_publisher_key",
            return_value=None,
        ), patch.object(app_module.requests, "post") as post:
            response = self.client.post("/publish-to-wol", json=WEEK_PAYLOAD)

        self.assertEqual(response.status_code, 400)
        self.assertIn("non è collegato", response.get_json()["error"])
        post.assert_not_called()

    def test_week_payload_is_serialized_and_sent_to_wol(self):
        response_mock = Mock()
        response_mock.ok = True
        response_mock.json.return_value = {
            "public_id": "abc123",
            "url": "https://example.workers.dev/p/abc123",
        }

        with patch.object(
            app_module,
            "get_wol_creator_token",
            return_value="creator-secret",
        ), patch.object(
            app_module,
            "get_wol_publisher_key",
            return_value="publisher-secret",
        ), patch.object(
            app_module.requests,
            "post",
            return_value=response_mock,
        ) as post:
            response = self.client.post("/publish-to-wol", json=WEEK_PAYLOAD)

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(
            data["url"],
            "https://example.workers.dev/p/abc123",
        )

        kwargs = post.call_args.kwargs
        self.assertEqual(
            kwargs["headers"]["Authorization"],
            "Bearer creator-secret",
        )
        self.assertEqual(kwargs["json"]["title"], "Settimana Test")
        self.assertEqual(len(kwargs["json"]["items"]), 2)

        first_snapshot = kwargs["json"]["items"][0]["workout"]
        self.assertEqual(first_snapshot["name"], "Facile")
        self.assertEqual(first_snapshot["steps"][0]["role"], "warmup")
        self.assertEqual(first_snapshot["steps"][0]["end_type"], "distance")
        self.assertEqual(first_snapshot["steps"][0]["preferred_unit"], "km")
        self.assertEqual(first_snapshot["steps"][0]["target"]["kind"], "none")

        second_snapshot = kwargs["json"]["items"][1]["workout"]
        repeat = second_snapshot["steps"][0]
        self.assertEqual(repeat["repetitions"], 2)
        self.assertEqual(
            repeat["steps"][0]["target"]["kind"],
            "pace_range",
        )
        self.assertEqual(
            repeat["steps"][1]["target"]["kind"],
            "heart_rate_zone",
        )

    def test_wol_error_is_returned_as_bad_gateway(self):
        response_mock = Mock()
        response_mock.ok = False
        response_mock.status_code = 401
        response_mock.text = '{"error":"unauthorized"}'

        with patch.object(
            app_module,
            "get_wol_creator_token",
            return_value="bad-secret",
        ), patch.object(
            app_module,
            "get_wol_publisher_key",
            return_value=None,
        ), patch.object(
            app_module.requests,
            "post",
            return_value=response_mock,
        ):
            response = self.client.post("/publish-to-wol", json=WEEK_PAYLOAD)

        self.assertEqual(response.status_code, 502)
        self.assertIn("HTTP 401", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
