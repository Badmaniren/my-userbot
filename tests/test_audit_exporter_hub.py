import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import ast

from skills.audit_exporter_hub import (
    AuditExporterHub,
    export_and_audit_reports,
    process_audit_stream
)
from skills.code_validator import CodeValidator, CodeValidatorASTError

class TestAuditExporterHubInquisition(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/repo_{uuid.uuid4().hex}"
        self.rand_log = f"/tmp/log_{uuid.uuid4().hex}.log"
        self.rand_threshold = round(random.uniform(0.1, 0.9), 2)
        self.exporter = AuditExporterHub(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

    def test_init_composition_defaults(self):
        self.assertEqual(self.exporter.audit_hub.repo_path, self.rand_repo)
        self.assertEqual(self.exporter.audit_hub.log_path, self.rand_log)
        self.assertEqual(self.exporter.audit_hub.threshold, self.rand_threshold)
        self.assertIsNotNone(self.exporter.logger)

    def test_export_reports_execution(self):
        rand_status = uuid.uuid4().hex
        with patch.object(self.exporter.audit_hub, 'generate_final_report', return_value={"status": rand_status}) as mock_gen, \
             patch.object(self.exporter.logger, 'get_structured_report', return_value=[]) as mock_get_struct:

            res = self.exporter.export_reports()
            mock_gen.assert_called_once()
            mock_get_struct.assert_called_once()
            self.assertEqual(res.get("status"), rand_status)

    def test_export_and_audit_reports_wrapper(self):
        rand_metric = uuid.uuid4().hex
        with patch('skills.audit_exporter_hub.AnomalyAuditHub') as MockHubClass:
            instance = MockHubClass.return_value
            instance.generate_final_report.return_value = {"metric": rand_metric}

            res = export_and_audit_reports(repo_path=self.rand_repo, log_path=self.rand_log, threshold=self.rand_threshold)
            MockHubClass.assert_called_once_with(repo_path=self.rand_repo, log_path=self.rand_log, threshold=self.rand_threshold)
            self.assertEqual(res.get("metric"), rand_metric)

    def test_process_audit_stream_logging(self):
        rand_source = uuid.uuid4().hex
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_details = uuid.uuid4().hex
        rand_telemetry = {"cpu": random.randint(1, 100)}

        with patch('skills.audit_exporter_hub.AnomalyLogger') as MockLoggerClass:
            mock_logger_inst = MockLoggerClass.return_value

            res = process_audit_stream(
                source=rand_source,
                severity=rand_severity,
                details=rand_details,
                telemetry_data=rand_telemetry
            )

            self.assertTrue(res)
            mock_logger_inst.log_anomaly.assert_called_once_with(
                source=rand_source,
                severity=rand_severity,
                details=rand_details,
                telemetry_snapshot=rand_telemetry
            )

    def test_code_validator_syntax_error_fix_and_handling(self):
        validator = CodeValidator()
        rand_var_name = f"var_{uuid.uuid4().hex[:6]}"
        valid_code_snippet = f"def {rand_var_name}():\n    return {random.randint(100, 999)}"

        res = validator.validate_code(valid_code_snippet)
        self.assertTrue(res)

        invalid_code_snippet = "class 45303b24:\n    pass"
        with self.assertRaises(CodeValidatorASTError):
            validator.validate_code(invalid_code_snippet)

if __name__ == '__main__':
    unittest.main()