import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.audit_export_pipeline import AuditExportPipeline
from skills.digest_exporter import DigestExporterError
from skills.code_validator import CodeValidatorASTError

class TestAuditExportPipelineInquisition(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.log_path = f"/logs/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 0.9)
        self.output_json = f"/out/{uuid.uuid4().hex}.json"
        self.output_html = f"/out/{uuid.uuid4().hex}.html"

    @patch("skills.audit_export_pipeline.AnomalyAuditHub")
    @patch("skills.audit_export_pipeline.DigestExporter")
    def test_run_audit_and_export_json_success(self, mock_digest_exporter_cls, mock_audit_hub_cls):
        mock_hub_instance = mock_audit_hub_cls.return_value
        mock_exporter_instance = mock_digest_exporter_cls.return_value
        expected_path = f"/result/{uuid.uuid4().hex}.json"
        mock_exporter_instance.export_json_report.return_value = expected_path

        pipeline = AuditExportPipeline(self.repo_path, self.log_path, self.threshold)
        result_path = pipeline.run_audit_and_export_json(self.output_json)

        mock_hub_instance.generate_final_report.assert_called_once()
        mock_exporter_instance.export_json_report.assert_called_once_with(self.output_json)
        self.assertEqual(result_path, expected_path)

    @patch("skills.audit_export_pipeline.AnomalyAuditHub")
    @patch("skills.audit_export_pipeline.DigestExporter")
    def test_run_audit_and_export_html_success(self, mock_digest_exporter_cls, mock_audit_hub_cls):
        mock_hub_instance = mock_audit_hub_cls.return_value
        mock_exporter_instance = mock_digest_exporter_cls.return_value
        expected_path = f"/result/{uuid.uuid4().hex}.html"
        mock_exporter_instance.export_html_report.return_value = expected_path

        pipeline = AuditExportPipeline(self.repo_path, self.log_path, self.threshold)
        result_path = pipeline.run_audit_and_export_html(self.output_html)

        mock_hub_instance.generate_final_report.assert_called_once()
        mock_exporter_instance.export_html_report.assert_called_once_with(self.output_html)
        self.assertEqual(result_path, expected_path)

    @patch("skills.audit_export_pipeline.AnomalyAuditHub")
    @patch("skills.audit_export_pipeline.DigestExporter")
    def test_aggregate_metric_delegation(self, mock_digest_exporter_cls, mock_audit_hub_cls):
        mock_hub_instance = mock_audit_hub_cls.return_value
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = random.uniform(1.0, 100.0)

        pipeline = AuditExportPipeline(self.repo_path, self.log_path, self.threshold)
        pipeline.aggregate_metric(metric_name, metric_value)

        mock_hub_instance.aggregate_and_report.assert_called_once_with(metric_name, metric_value)

    @patch("skills.audit_export_pipeline.AnomalyAuditHub")
    @patch("skills.audit_export_pipeline.DigestExporter")
    def test_log_pipeline_anomaly_delegation(self, mock_digest_exporter_cls, mock_audit_hub_cls):
        mock_hub_instance = mock_audit_hub_cls.return_value
        source = f"source_{uuid.uuid4().hex[:6]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {"error_code": random.randint(100, 999)}
        telemetry = {"cpu_usage": random.uniform(0.0, 100.0)}

        pipeline = AuditExportPipeline(self.repo_path, self.log_path, self.threshold)
        pipeline.log_pipeline_anomaly(source, severity, details, telemetry)

        mock_hub_instance.log_anomaly.assert_called_once_with(source, severity, details, telemetry)

    @patch("skills.audit_export_pipeline.AnomalyAuditHub")
    @patch("skills.audit_export_pipeline.DigestExporter")
    def test_export_report_formats(self, mock_digest_exporter_cls, mock_audit_hub_cls):
        mock_hub_instance = mock_audit_hub_cls.return_value
        mock_exporter_instance = mock_digest_exporter_cls.return_value

        json_result_path = f"/reports/{uuid.uuid4().hex}.json"
        html_result_path = f"/reports/{uuid.uuid4().hex}.html"
        mock_exporter_instance.export_json_report.return_value = json_result_path
        mock_exporter_instance.export_html_report.return_value = html_result_path

        pipeline = AuditExportPipeline(self.repo_path, self.log_path, self.threshold)

        res_json = pipeline.export_report(self.output_json, format="json")
        self.assertEqual(res_json, json_result_path)
        mock_exporter_instance.export_json_report.assert_called_with(self.output_json)

        res_html = pipeline.export_report(self.output_html, format="HTML")
        self.assertEqual(res_html, html_result_path)
        mock_exporter_instance.export_html_report.assert_called_with(self.output_html)

        res_default = pipeline.export_report(self.output_json, format=uuid.uuid4().hex)
        self.assertEqual(res_default, json_result_path)

    @patch("skills.audit_export_pipeline.AnomalyAuditHub")
    @patch("skills.audit_export_pipeline.DigestExporter")
    def test_export_report_raises_exporter_error(self, mock_digest_exporter_cls, mock_audit_hub_cls):
        mock_exporter_instance = mock_digest_exporter_cls.return_value
        mock_exporter_instance.export_json_report.side_effect = DigestExporterError(f"Error {uuid.uuid4().hex}")

        pipeline = AuditExportPipeline(self.repo_path, self.log_path, self.threshold)
        with self.assertRaises(DigestExporterError):
            pipeline.run_audit_and_export_json(self.output_json)

    def test_code_validator_safe_parsing_integration(self):
        from skills.code_validator import CodeValidator
        validator = CodeValidator()
        safe_code = f"def secure_func_{uuid.uuid4().hex[:6]}():\n    x = 0o123\n    return x"
        result = validator.validate_code(safe_code)
        self.assertIsNotNone(result)

    def test_code_validator_syntax_error_handling(self):
        from skills.code_validator import CodeValidator
        validator = CodeValidator()
        malformed_code = f"class {uuid.uuid4().hex[:6]}:\n    pass\n    0123"
        with self.assertRaises(CodeValidatorASTError):
            validator.validate_code(malformed_code)

    def test_stream_io_mocking_compliance(self):
        stream_data = f"telemetry_stream_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(stream_data)
        content = mock_stream.read()
        self.assertEqual(content, stream_data)