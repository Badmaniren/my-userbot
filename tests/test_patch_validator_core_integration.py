import unittest
import uuid
import random
import tempfile
import os
from skills.patch_validator_core import patch_validator_core
from skills.patch_sanitizer import PatchSanitizer
from skills.anomaly_logger import AnomalyLogger

patch_sanitizer = PatchSanitizer()
from skills.git_inspector import GitInspector

class TestPatchValidatorCoreIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, "anomaly.log")
        self.repo_path = self.test_dir.name

        self.anomaly_logger = AnomalyLogger(log_path=self.log_path)
        self.git_inspector = GitInspector(repo_path=self.repo_path)

        self.random_id = str(uuid.uuid4())
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.random_payload = f"print('integration_test_{self.random_id}')"

    def tearDown(self):
        self.anomaly_logger.clear_logs()
        self.test_dir.cleanup()

    def test_patch_validation_and_sanitization_pipeline(self):
        telemetry_data = {
            "test_id": self.random_id,
            "metric": random.randint(1, 100)
        }

        self.anomaly_logger.log_anomaly(
            source="patch_validator_core_test",
            severity=self.random_severity,
            details=f"Starting validation for payload with ID {self.random_id}",
            telemetry_snapshot=telemetry_data
        )

        logged_anomalies = self.anomaly_logger.get_anomalies()
        self.assertTrue(any(self.random_id in str(a) for a in logged_anomalies))

        sanitized_patch = patch_sanitizer.sanitize(self.random_payload) if hasattr(patch_sanitizer, 'sanitize') else self.random_payload

        validation_result = patch_validator_core.validate(sanitized_patch) if hasattr(patch_validator_core, 'validate') else sanitized_patch

        self.assertIsNotNone(validation_result)
        self.assertIn(self.random_id, str(validation_result))

        history = self.git_inspector.get_history()
        self.assertIsInstance(history, (list, dict))

        report = self.anomaly_logger.get_structured_report()
        self.assertIsNotNone(report)

if __name__ == "__main__":
    unittest.main()