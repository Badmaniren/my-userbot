import io
import os
import random
import string
import unittest
from unittest.mock import MagicMock, patch

import skills.repo_security_gate_validator as rsgv_module
from skills.repo_security_gate_validator import (
    RepoSecurityGateValidator,
    validate_repo_security_gate,
)
from skills.repo_health_metric_validator import MetricValidationError


def generate_random_string(prefix="", length=8):
    token = "".join(random.choices(string.ascii_letters + string.digits, k=length))
    return f"{prefix}_{token}" if prefix else token


def generate_random_metrics():
    return {
        generate_random_string("metric"): random.uniform(0.1, 99.9),
        generate_random_string("status"): generate_random_string("state"),
        generate_random_string("count"): random.randint(1, 1000),
    }


class TestRepoSecurityGateValidator(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/repos/{generate_random_string('path')}/{generate_random_string('repo')}"
        self.security_token = generate_random_string("sec_token")
        self.health_token = generate_random_string("hlth_token")

    def test_validator_initialization(self):
        validator = RepoSecurityGateValidator(repo_path=self.random_repo_path)
        self.assertEqual(validator.repo_path, self.random_repo_path)

    def test_gate_passes_when_security_and_health_are_valid(self):
        metrics_data = generate_random_metrics()
        expected_scan_id = generate_random_string("scan_id")

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_health_cls:

            mock_sec_instance = mock_sec_cls.return_value
            mock_sec_instance.scan_and_evaluate.return_value = {
                "status": "PASS",
                "passed": True,
                "scan_id": expected_scan_id,
                "vulnerabilities": [],
                "security_token": self.security_token,
            }

            mock_health_instance = mock_health_cls.return_value
            mock_health_instance.validate.return_value = True

            validator = RepoSecurityGateValidator(repo_path=self.random_repo_path)
            result = validator.validate_gate(metrics_data)

            mock_sec_cls.assert_called_with(self.random_repo_path)
            mock_sec_instance.scan_and_evaluate.assert_called_once()
            mock_health_instance.validate.assert_called_once_with(metrics_data)

            self.assertTrue(result.get("passed"))
            self.assertFalse(result.get("blocked"))
            self.assertEqual(result.get("security_evaluation", {}).get("scan_id"), expected_scan_id)
            self.assertEqual(result.get("security_evaluation", {}).get("security_token"), self.security_token)
            self.assertTrue(result.get("health_evaluation", {}).get("valid"))

    def test_gate_blocks_when_security_check_fails(self):
        metrics_data = generate_random_metrics()
        critical_cve = f"CVE-{random.randint(2020, 2026)}-{random.randint(1000, 9999)}"
        sec_failure_reason = f"Critical vulnerability detected: {critical_cve}"

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_health_cls:

            mock_sec_instance = mock_sec_cls.return_value
            mock_sec_instance.scan_and_evaluate.return_value = {
                "status": "FAIL",
                "passed": False,
                "vulnerabilities": [critical_cve],
                "reason": sec_failure_reason,
            }

            mock_health_instance = mock_health_cls.return_value
            mock_health_instance.validate.return_value = True

            validator = RepoSecurityGateValidator(repo_path=self.random_repo_path)
            result = validator.validate_gate(metrics_data)

            self.assertFalse(result.get("passed"))
            self.assertTrue(result.get("blocked"))
            self.assertIn(sec_failure_reason, str(result.get("errors", [])) + str(result.get("reasons", [])))
            self.assertIn(critical_cve, result.get("security_evaluation", {}).get("vulnerabilities", []))

    def test_gate_blocks_when_health_metrics_validation_fails(self):
        metrics_data = generate_random_metrics()
        health_error_message = f"Metric drift detected: {generate_random_string('metric_anomaly')}"

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_health_cls:

            mock_sec_instance = mock_sec_cls.return_value
            mock_sec_instance.scan_and_evaluate.return_value = {
                "status": "PASS",
                "passed": True,
                "vulnerabilities": [],
            }

            mock_health_instance = mock_health_cls.return_value
            mock_health_instance.validate.side_effect = MetricValidationError(health_error_message)

            validator = RepoSecurityGateValidator(repo_path=self.random_repo_path)
            result = validator.validate_gate(metrics_data)

            self.assertFalse(result.get("passed"))
            self.assertTrue(result.get("blocked"))
            all_errors = str(result.get("errors", [])) + str(result.get("reasons", []))
            self.assertIn(health_error_message, all_errors)

    def test_gate_blocks_when_both_security_and_health_fail(self):
        metrics_data = generate_random_metrics()
        critical_cve = f"CVE-{random.randint(2020, 2026)}-{random.randint(1000, 9999)}"
        health_error_message = f"Health check failed on key: {generate_random_string('err_metric')}"

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_health_cls:

            mock_sec_instance = mock_sec_cls.return_value
            mock_sec_instance.scan_and_evaluate.return_value = {
                "status": "FAIL",
                "passed": False,
                "vulnerabilities": [critical_cve],
            }

            mock_health_instance = mock_health_cls.return_value
            mock_health_instance.validate.side_effect = MetricValidationError(health_error_message)

            validator = RepoSecurityGateValidator(repo_path=self.random_repo_path)
            result = validator.validate_gate(metrics_data)

            self.assertFalse(result.get("passed"))
            self.assertTrue(result.get("blocked"))

            failures_recorded = str(result.get("errors", [])) + str(result.get("reasons", []))
            self.assertIn(critical_cve, str(result.get("security_evaluation", {})))
            self.assertIn(health_error_message, failures_recorded)

    def test_gate_validates_stream_payload(self):
        stream_payload = os.urandom(random.randint(64, 128))
        stream_io = io.BytesIO(stream_payload)
        parsed_stream_item = {generate_random_string("k"): generate_random_string("v")}

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator") as mock_health_cls:

            mock_sec_instance = mock_sec_cls.return_value
            mock_sec_instance.scan_and_evaluate.return_value = {
                "status": "PASS",
                "passed": True,
            }

            mock_health_instance = mock_health_cls.return_value
            mock_health_instance.validate_stream.return_value = [parsed_stream_item]
            mock_health_instance.validate.return_value = True

            validator = RepoSecurityGateValidator(repo_path=self.random_repo_path)
            result = validator.validate_stream_gate(stream_io)

            mock_health_instance.validate_stream.assert_called_once_with(stream_io)
            self.assertTrue(result.get("passed"))
            self.assertFalse(result.get("blocked"))

    def test_validate_repo_security_gate_convenience_function(self):
        metrics_data = generate_random_metrics()
        random_repo = f"/repos/{generate_random_string('org')}/{generate_random_string('repo')}"
        unique_run_token = generate_random_string("run_token")

        with patch.object(RepoSecurityGateValidator, "validate_gate") as mock_val_method:
            mock_val_method.return_value = {
                "passed": True,
                "blocked": False,
                "token": unique_run_token,
            }

            result = validate_repo_security_gate(repo_path=random_repo, metrics_data=metrics_data)

            self.assertTrue(result.get("passed"))
            self.assertFalse(result.get("blocked"))
            self.assertEqual(result.get("token"), unique_run_token)
            mock_val_method.assert_called_once_with(metrics_data)

    def test_fail_closed_on_unexpected_gateway_exception(self):
        metrics_data = generate_random_metrics()
        unexpected_error_text = f"Fatal system fault: {generate_random_string('crash')}"

        with patch("skills.repo_security_gate_validator.RepoSecurityGateway") as mock_sec_cls, \
             patch("skills.repo_security_gate_validator.RepoHealthMetricValidator"):

            mock_sec_instance = mock_sec_cls.return_value
            mock_sec_instance.scan_and_evaluate.side_effect = RuntimeError(unexpected_error_text)

            validator = RepoSecurityGateValidator(repo_path=self.random_repo_path)
            result = validator.validate_gate(metrics_data)

            self.assertFalse(result.get("passed"))
            self.assertTrue(result.get("blocked"))
            errors_str = str(result.get("errors", [])) + str(result.get("reasons", []))
            self.assertIn(unexpected_error_text, errors_str)


if __name__ == "__main__":
    unittest.main()