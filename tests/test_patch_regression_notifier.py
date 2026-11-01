import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import datetime
import requests
from skills.patch_regression_notifier import (
    PatchRegressionNotifier,
    PatchRegressionNotifierError,
    send_regression_notification
)

class TestPatchRegressionNotifierInquisition(unittest.TestCase):
    def setUp(self):
        self.channel_name = f"channel-{uuid.uuid4().hex[:8]}"
        self.webhook_url = f"https://api.{uuid.uuid4().hex[:6]}.net/webhook"
        self.patch_id = f"patch-{uuid.uuid4().hex[:8]}"
        self.status = random.choice(["PASSED", "FAILED", "WARNING", "SKIPPED"])
        self.summary = f"Summary report generated at {uuid.uuid4().hex[:6]}"
        self.notifier = PatchRegressionNotifier(channel=self.channel_name, webhook_url=self.webhook_url)

    def test_format_payload_structure_and_values(self):
        payload = self.notifier._format_payload(self.patch_id, self.status, self.summary)
        self.assertEqual(payload["channel"], self.channel_name)
        self.assertEqual(payload["patch_id"], self.patch_id)
        self.assertEqual(payload["status"], self.status)
        self.assertEqual(payload["summary"], self.summary)
        self.assertIn("timestamp", payload)
        self.assertIsInstance(payload["timestamp"], str)

    def test_send_notification_success(self):
        with patch("skills.patch_regression_notifier.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = self.notifier.send_notification(self.patch_id, self.status, self.summary)
            self.assertTrue(result)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], self.webhook_url)
            self.assertEqual(kwargs["json"]["patch_id"], self.patch_id)
            self.assertEqual(kwargs["json"]["status"], self.status)

    def test_send_notification_failure_raises_custom_exception(self):
        with patch("skills.patch_regression_notifier.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException(f"Connection timeout {uuid.uuid4().hex[:4]}")

            with self.assertRaises(PatchRegressionNotifierError) as ctx:
                self.notifier.send_notification(self.patch_id, self.status, self.summary)
            self.assertIn("Failed to send notification", str(ctx.exception))

    def test_batch_notify_execution(self):
        patches_data = [
            {
                "patch_id": f"patch-{uuid.uuid4().hex[:6]}",
                "status": random.choice(["PASSED", "FAILED"]),
                "summary": f"Report {uuid.uuid4().hex[:4]}"
            },
            {
                "patch_id": f"patch-{uuid.uuid4().hex[:6]}",
                "status": random.choice(["PASSED", "FAILED"]),
                "summary": f"Report {uuid.uuid4().hex[:4]}"
            }
        ]

        with patch("skills.patch_regression_notifier.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            results = self.notifier.batch_notify(patches_data)
            self.assertEqual(len(results), 2)
            self.assertTrue(all(results))
            self.assertEqual(mock_post.call_count, 2)

    def test_send_regression_notification_helper_with_dict_report(self):
        trace_id = f"trace-{uuid.uuid4().hex[:8]}"
        metric_name = f"metric-{uuid.uuid4().hex[:6]}"
        metric_value = random.randint(10, 1000)
        history_count = random.randint(1, 50)
        report_summary_text = f"Custom summary {uuid.uuid4().hex[:6]}"

        payload = {
            "trace_id": trace_id,
            "metric": metric_name,
            "value": metric_value,
            "history_count": history_count,
            "report": {
                "summary": report_summary_text
            }
        }

        with patch("skills.patch_regression_notifier.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = send_regression_notification(payload)
            self.assertTrue(result)

            called_json = mock_post.call_args[1]["json"]
            self.assertEqual(called_json["channel"], trace_id)
            self.assertEqual(called_json["patch_id"], trace_id)
            self.assertEqual(called_json["status"], "PASSED")
            self.assertEqual(called_json["summary"], report_summary_text)

    def test_send_regression_notification_helper_with_non_dict_report(self):
        trace_id = f"trace-{uuid.uuid4().hex[:8]}"
        metric_name = f"metric-{uuid.uuid4().hex[:6]}"
        metric_value = random.randint(1, 500)
        history_count = random.randint(1, 10)

        payload = {
            "trace_id": trace_id,
            "metric": metric_name,
            "value": metric_value,
            "history_count": history_count,
            "report": f"string-report-{uuid.uuid4().hex[:4]}"
        }

        with patch("skills.patch_regression_notifier.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = send_regression_notification(payload)
            self.assertTrue(result)

            called_json = mock_post.call_args[1]["json"]
            self.assertEqual(called_json["channel"], trace_id)
            self.assertEqual(called_json["patch_id"], trace_id)
            self.assertEqual(called_json["status"], "PASSED")
            self.assertIn(metric_name, called_json["summary"])
            self.assertIn(str(metric_value), called_json["summary"])
            self.assertIn(str(history_count), called_json["summary"])

    def test_send_regression_notification_helper_missing_fields_defaults(self):
        payload = {}

        with patch("skills.patch_regression_notifier.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = send_regression_notification(payload)
            self.assertTrue(result)

            called_json = mock_post.call_args[1]["json"]
            self.assertEqual(called_json["channel"], "default-channel")
            self.assertEqual(called_json["patch_id"], "integration-patch")
            self.assertEqual(called_json["status"], "PASSED")

if __name__ == "__main__":
    unittest.main()