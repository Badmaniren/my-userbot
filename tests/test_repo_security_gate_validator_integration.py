import os
import random
import tempfile
import unittest
import uuid
from pathlib import Path

from skills.repo_health_metric_validator import (
    MetricValidationError,
    RepoHealthMetricValidator,
)
from skills.repo_security_gate_validator import RepoSecurityGateValidator
from skills.repo_security_gateway import RepoSecurityGateway


class TestRepoSecurityGateValidatorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = self.temp_dir_obj.name
        self.random_token = uuid.uuid4().hex
        self.random_file_name = f"source_{self.random_token[:8]}.py"
        self.source_file = Path(self.temp_dir) / self.random_file_name
        self.source_file.write_text(
            f"# Clean module {self.random_token}\ndef execute():\n    return True\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def test_validate_gate_successful_release(self):
        unique_run_id = f"run_{uuid.uuid4().hex}"
        random_score = round(random.uniform(85.0, 99.0), 2)
        valid_metrics = {
            "run_id": unique_run_id,
            "health_score": random_score,
            "status": "healthy",
            "coverage": 92.5,
        }

        validator = RepoSecurityGateValidator(repo_path=self.temp_dir)
        result = validator.validate_gate(metrics_data=valid_metrics)

        self.assertIsInstance(result, dict)
        self.assertIn("allowed", result)
        self.assertTrue(result["allowed"])
        self.assertFalse(result.get("blocked", False))

        self.assertIn("security_gate", result)
        self.assertIsInstance(result["security_gate"], dict)

        self.assertIn("health_evaluation", result)
        self.assertEqual(result.get("run_id"), unique_run_id)

    def test_validate_gate_blocks_release_on_unhealthy_metrics(self):
        unique_bad_id = f"fail_{uuid.uuid4().hex}"
        unhealthy_metrics = {
            "run_id": unique_bad_id,
            "health_score": random.uniform(5.0, 20.0),
            "status": "critical",
            "coverage": 15.0,
        }

        validator = RepoSecurityGateValidator(repo_path=self.temp_dir)
        result = validator.validate_gate(metrics_data=unhealthy_metrics)

        self.assertIsInstance(result, dict)
        self.assertIn("allowed", result)
        self.assertFalse(result["allowed"])
        self.assertTrue(result.get("blocked", True))
        self.assertIn("failures", result)
        self.assertTrue(len(result["failures"]) > 0)
        self.assertEqual(result.get("run_id"), unique_bad_id)

    def test_validate_gate_records_failures_on_corrupted_payload(self):
        random_corrupt_id = uuid.uuid4().hex
        corrupted_metrics = {
            "invalid_key": random_corrupt_id,
            "health_score": "not_a_number",
        }

        validator = RepoSecurityGateValidator(repo_path=self.temp_dir)
        result = validator.validate_gate(metrics_data=corrupted_metrics)

        self.assertIsInstance(result, dict)
        self.assertFalse(result["allowed"])
        self.assertTrue(result.get("blocked", True))
        self.assertIn("audit_record", result)
        self.assertIn(random_corrupt_id, str(result))


if __name__ == "__main__":
    unittest.main()