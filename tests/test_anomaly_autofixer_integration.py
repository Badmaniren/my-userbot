import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_autofixer import AnomalyAutofixer, AnomalyAutofixerError, autofix_anomalies


class TestIntegrationAnomalyAutofixer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.log_file = os.path.join(self.repo_path, f"audit_{uuid.uuid4().hex}.log")
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.autofixer = AnomalyAutofixer(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_dispatch_and_fix_integration(self):
        source = f"source_{uuid.uuid4().hex[:6]}"
        severity = random.choice(["CRITICAL", "HIGH", "ERROR"])
        details = {"error_code": random.randint(500, 599), "message": uuid.uuid4().hex}
        telemetry_snapshot = {"cpu_load": random.random(), "memory_usage": random.randint(1024, 8192)}

        patch_id = self.autofixer.dispatch_and_fix(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertIsNotNone(patch_id)

        log_content = self.autofixer.analyze_log_stream()
        self.assertGreater(len(log_content), 0)
        self.assertTrue(os.path.exists(self.log_file))

    def test_autofix_anomalies_function_integration(self):
        report_key = uuid.uuid4().hex
        audit_report = {report_key: random.randint(1, 100)}
        metadata = {"run_id": uuid.uuid4().hex, "mode": "auto"}

        result = autofix_anomalies(
            repo_path=self.repo_path,
            audit_report=audit_report,
            metadata=metadata
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["repo_path"], self.repo_path)
        self.assertIn(report_key, result["report_keys"])
        self.assertEqual(result["metadata"], metadata)
        self.assertIsNotNone(result["patch_id"])


if __name__ == "__main__":
    unittest.main()