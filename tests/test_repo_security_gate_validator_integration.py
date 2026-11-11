import io
import json
import os
import shutil
import tempfile
import unittest
import uuid

from skills.repo_security_gate_validator import (
    RepoSecurityGateValidator,
    validate_repo_security_gate,
)
from skills.repo_health_metric_validator import (
    RepoHealthMetricValidator,
    MetricValidationError,
)
from skills.repo_security_gateway import RepoSecurityGateway


class TestRepoSecurityGateValidatorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="repo_sec_gate_test_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_gate_contract_and_run_id_propagation(self):
        random_run_id = f"run-{uuid.uuid4().hex}"
        random_metric_name = f"metric-{uuid.uuid4().hex[:8]}"
        metrics_payload = {
            "run_id": random_run_id,
            "metric_name": random_metric_name,
            "status": "passed",
            "coverage": 95.5,
        }

        validator = RepoSecurityGateValidator(repo_path=self.temp_dir)
        self.assertIsInstance(validator.security_gateway, RepoSecurityGateway)
        self.assertIsInstance(validator.health_validator, RepoHealthMetricValidator)

        result = validator.validate_gate(metrics_payload)

        self.assertIsInstance(result, dict)
        self.assertIn("passed", result)
        self.assertIn("allowed", result)
        self.assertIn("blocked", result)
        self.assertIn("security_evaluation", result)
        self.assertIn("security_gate", result)
        self.assertIn("health_evaluation", result)
        self.assertIn("errors", result)
        self.assertIn("reasons", result)
        self.assertIn("failures", result)
        self.assertIn("audit_record", result)

        self.assertEqual(result.get("run_id"), random_run_id)
        self.assertIn(random_run_id, result["audit_record"])
        self.assertEqual(result["blocked"], not result["passed"])
        self.assertEqual(result["allowed"], result["passed"])
        self.assertIsInstance(result["errors"], list)
        self.assertIsInstance(result["reasons"], list)
        self.assertIsInstance(result["failures"], list)

    def test_validate_repo_security_gate_function(self):
        random_run_id = f"func-run-{uuid.uuid4().hex}"
        metrics_payload = {
            "run_id": random_run_id,
            "score": 100,
        }

        result = validate_repo_security_gate(self.temp_dir, metrics_payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("run_id"), random_run_id)
        self.assertIn("security_gate", result)
        self.assertIn("health_evaluation", result)
        self.assertEqual(result["blocked"], not result["passed"])

    def test_validate_gate_with_nonexistent_repo_blocks_or_reports_failure(self):
        non_existent_path = os.path.join(self.temp_dir, f"missing_{uuid.uuid4().hex}")
        random_run_id = f"err-run-{uuid.uuid4().hex}"
        metrics_payload = {"run_id": random_run_id}

        validator = RepoSecurityGateValidator(repo_path=non_existent_path)
        result = validator.validate_gate(metrics_payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("run_id"), random_run_id)
        self.assertIsInstance(result["passed"], bool)
        self.assertEqual(result["blocked"], not result["passed"])
        self.assertIn("security_evaluation", result)
        self.assertIn("health_evaluation", result)

    def test_validate_stream_gate_integration(self):
        random_run_id = f"stream-run-{uuid.uuid4().hex}"
        sample_metrics = [{"run_id": random_run_id, "score": 90}]
        stream = io.StringIO(json.dumps(sample_metrics))

        validator = RepoSecurityGateValidator(repo_path=self.temp_dir)
        result = validator.validate_stream_gate(stream)

        self.assertIsInstance(result, dict)
        self.assertIn("passed", result)
        self.assertIn("blocked", result)
        self.assertEqual(result["blocked"], not result["passed"])
        self.assertIn("security_evaluation", result)
        self.assertIn("health_evaluation", result)


if __name__ == "__main__":
    unittest.main()