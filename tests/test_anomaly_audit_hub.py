import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import ast

from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.code_validator import CodeValidator, CodeValidatorASTError


class TestAnomalyAuditHubAndCodeValidator(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/repo_{uuid.uuid4().hex[:8]}"
        self.rand_log = f"/tmp/log_{uuid.uuid4().hex[:8]}.log"
        self.rand_threshold = round(random.uniform(0.1, 0.9), 2)
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )
        self.validator = CodeValidator(repo_path=self.rand_repo)

    def test_log_anomaly_success(self):
        source = f"source_{uuid.uuid4().hex[:6]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {uuid.uuid4().hex[:4]: uuid.uuid4().hex[:4]}
        telemetry_snapshot = {uuid.uuid4().hex[:4]: random.randint(1, 100)}

        with patch.object(self.audit_hub.logger, 'log_anomaly', return_value=None) as mock_log:
            res = self.audit_hub.log_anomaly(source, severity, details, telemetry_snapshot)
            mock_log.assert_called_once_with(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
            self.assertEqual(res, {"status": "logged", "source": source})

    def test_log_anomaly_with_explicit_result(self):
        source = f"source_{uuid.uuid4().hex[:6]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {uuid.uuid4().hex[:4]: uuid.uuid4().hex[:4]}
        telemetry_snapshot = {uuid.uuid4().hex[:4]: random.randint(1, 100)}
        expected_ret = {"custom_status": uuid.uuid4().hex}

        with patch.object(self.audit_hub.logger, 'log_anomaly', return_value=expected_ret) as mock_log:
            res = self.audit_hub.log_anomaly(source, severity, details, telemetry_snapshot)
            mock_log.assert_called_once()
            self.assertEqual(res, expected_ret)

    def test_aggregate_and_report_success(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        value = round(random.uniform(10.0, 500.0), 2)

        with patch.object(self.audit_hub.aggregator, 'aggregate_and_report', return_value=None) as mock_agg:
            res = self.audit_hub.aggregate_and_report(metric_name, value)
            mock_agg.assert_called_once_with(
                metric_name=metric_name,
                value=value
            )
            self.assertEqual(res, {"metric_status": "reported", "metric_name": metric_name, "value": value})

    def test_aggregate_and_report_with_explicit_result(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        value = round(random.uniform(10.0, 500.0), 2)
        expected_ret = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.audit_hub.aggregator, 'aggregate_and_report', return_value=expected_ret) as mock_agg:
            res = self.audit_hub.aggregate_and_report(metric_name, value)
            mock_agg.assert_called_once()
            self.assertEqual(res, expected_ret)

    def test_generate_final_report_success(self):
        with patch.object(self.audit_hub.aggregator, 'generate_final_report', return_value=None) as mock_gen:
            res = self.audit_hub.generate_final_report()
            mock_gen.assert_called_once()
            self.assertEqual(res, {"status": "success", "report": "generated"})

    def test_generate_final_report_with_explicit_result(self):
        expected_ret = {uuid.uuid4().hex: random.randint(100, 999)}

        with patch.object(self.audit_hub.aggregator, 'generate_final_report', return_value=expected_ret) as mock_gen:
            res = self.audit_hub.generate_final_report()
            mock_gen.assert_called_once()
            self.assertEqual(res, expected_ret)

    def test_code_validator_syntax_error_fix_simulation(self):
        valid_var = f"var_{uuid.uuid4().hex[:6]}"
        valid_val = random.randint(1, 1000)
        valid_code = f"{valid_var} = {valid_val}\n"

        parsed_result = self.validator.validate_code(valid_code)
        self.assertIsNotNone(parsed_result)

        invalid_code = f"class {uuid.uuid4().hex[:6]}:\n    pass\n"
        invalid_code_bad = "class 421bec0e:\n    pass\n"

        with self.assertRaises(CodeValidatorASTError):
            self.validator.validate_code(invalid_code_bad)


if __name__ == '__main__':
    unittest.main()