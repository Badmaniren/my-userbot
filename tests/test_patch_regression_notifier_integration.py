import unittest
import uuid
import random
from skills.patch_regression_notifier import PatchRegressionNotifier, send_regression_notification, PatchRegressionNotifierError

class TestPatchRegressionNotifierIntegration(unittest.TestCase):

    def test_patch_regression_notifier_workflow(self):
        unique_channel = f"channel-{uuid.uuid4()}"
        unique_patch_id = f"patch-{uuid.uuid4()}"
        random_value = round(random.uniform(1.0, 100.0), 2)

        notifier = PatchRegressionNotifier(
            channel=unique_channel,
            webhook_url="https://httpbin.org/post"
        )

        payload_dict = {
            "trace_id": unique_patch_id,
            "metric": "regression_latency",
            "value": random_value,
            "history_count": random.randint(5, 50),
            "report": {
                "summary": f"Integration test summary with random value {random_value}"
            }
        }

        formatted = notifier._format_payload(
            patch_id=unique_patch_id,
            regression_status="PASSED",
            report_summary=payload_dict["report"]["summary"]
        )

        self.assertEqual(formatted["channel"], unique_channel)
        self.assertEqual(formatted["patch_id"], unique_patch_id)
        self.assertEqual(formatted["status"], "PASSED")
        self.assertIn(str(random_value), formatted["summary"])
        self.assertIn("timestamp", formatted)

        batch_data = [
            {
                "patch_id": f"batch-patch-{uuid.uuid4()}",
                "status": "PASSED",
                "summary": f"Batch report {random.randint(1, 100)}"
            },
            {
                "patch_id": f"batch-patch-{uuid.uuid4()}",
                "status": "FAILED",
                "summary": f"Batch report {random.randint(101, 200)}"
            }
        ]

        batch_results = notifier.batch_notify(batch_data)
        self.assertEqual(len(batch_results), 2)
        self.assertTrue(all(isinstance(res, bool) for res in batch_results))

        helper_result = send_regression_notification(payload_dict)
        self.assertTrue(helper_result)

        with self.assertRaises(PatchRegressionNotifierError):
            bad_notifier = PatchRegressionNotifier(
                channel=unique_channel,
                webhook_url="https://invalid.nonexistentdomain-test.net/hook"
            )
            bad_notifier.send_notification(
                patch_id=unique_patch_id,
                regression_status="FAILED",
                report_summary="Trigger error"
            )

if __name__ == "__main__":
    unittest.main()