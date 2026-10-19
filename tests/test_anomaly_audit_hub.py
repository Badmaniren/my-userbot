import unittest
from unittest.mock import patch
import uuid
import random
import ast

from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.code_validator import CodeValidator, CodeValidatorASTError


class TestAnomalyAuditHubAndValidatorInquisition(unittest.TestCase):
    def setUp(self):
        self.repo_path_val = uuid.uuid4().hex
        self.log_path_val = f"{uuid.uuid4().hex}.log"
        self.threshold_val = round(random.uniform(0.1, 99.9), 2)
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path_val,
            log_path=self.log_path_val,
            threshold=self.threshold_val
        )
        self.validator = CodeValidator()

    def test_anomaly_audit_hub_lifecycle_and_arguments(self):
        source_id = uuid.uuid4().hex
        severity_val = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot_dict = {uuid.uuid4().hex: random.randint(1, 1000)}

        with patch("skills.anomaly_logger.AnomalyLogger.log_anomaly") as mock_log_anomaly:
            mock_log_anomaly.return_value = None
            log_res = self.hub.log_anomaly(
                source=source_id,
                severity=severity_val,
                details=details_dict,
                telemetry_snapshot=telemetry_snapshot_dict
            )
            self.assertTrue(log_res)
            mock_log_anomaly.assert_called_once_with(
                source=source_id,
                severity=severity_val,
                details=details_dict,
                telemetry_snapshot=telemetry_snapshot_dict
            )

        metric_name_val = uuid.uuid4().hex
        metric_value = round(random.uniform(0.0, 500.0), 2)

        with patch("skills.anomaly_report_aggregator.AnomalyReportAggregator.aggregate_and_report") as mock_agg_report:
            expected_agg_result = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_agg_report.return_value = expected_agg_result

            res = self.hub.aggregate_and_report(metric_name=metric_name_val, value=metric_value)
            self.assertEqual(res, expected_agg_result)
            mock_agg_report.assert_called_once_with(
                metric_name=metric_name_val,
                value=metric_value
            )

        with patch("skills.anomaly_report_aggregator.AnomalyReportAggregator.generate_final_report") as mock_gen_report:
            expected_final_report = {uuid.uuid4().hex: random.randint(1, 50)}
            mock_gen_report.return_value = expected_final_report

            final_res = self.hub.generate_final_report()
            self.assertEqual(final_res, expected_final_report)
            mock_gen_report.assert_called_once()

    def test_code_validator_syntax_error_inquisition(self):
        invalid_variable_name = f"var_{uuid.uuid4().hex[:6]}"
        invalid_code_snippet = f"class {invalid_variable_name}:\n    pass\n1 = 2"

        with self.assertRaises(CodeValidatorASTError) as ctx:
            self.validator.validate_code(invalid_code_snippet)

        self.assertIn("Ошибка синтаксиса AST", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()