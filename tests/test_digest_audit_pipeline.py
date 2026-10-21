import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.digest_audit_pipeline import DigestAuditPipeline, DigestAuditPipelineError


class TestDigestAuditPipeline(unittest.TestCase):
    def setUp(self):
        self.random_repo = f"/path/to/repo_{uuid.uuid4().hex[:8]}"
        self.random_log = f"/var/log/{uuid.uuid4().hex[:8]}.log"
        self.random_threshold = round(random.uniform(1.0, 10.0), 2)

        self.mock_audit_hub = MagicMock()
        self.mock_exporter = MagicMock()

        self.pipeline = DigestAuditPipeline(
            repo_path=self.random_repo,
            log_path=self.random_log,
            threshold=self.random_threshold,
            audit_hub=self.mock_audit_hub,
            exporter=self.mock_exporter
        )

    def test_init_default_dependencies(self):
        with patch("skills.digest_audit_pipeline.AnomalyAuditHub") as mock_hub_cls, \
             patch("skills.digest_audit_pipeline.DigestExporter") as mock_exp_cls:

            pipeline = DigestAuditPipeline(
                repo_path=self.random_repo,
                log_path=self.random_log,
                threshold=self.random_threshold
            )

            mock_hub_cls.assert_called_once_with(
                repo_path=self.random_repo,
                log_path=self.random_log,
                threshold=self.random_threshold
            )
            mock_exp_cls.assert_called_once()
            self.assertIsNotNone(pipeline.audit_hub)
            self.assertIsNotNone(pipeline.exporter)

    def test_log_anomaly(self):
        source = f"source_{uuid.uuid4().hex[:6]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {"msg": uuid.uuid4().hex}
        telemetry = {"cpu": random.randint(1, 100)}

        expected_result = uuid.uuid4().hex
        self.mock_audit_hub.log_anomaly.return_value = expected_result

        result = self.pipeline.log_anomaly(source, severity, details, telemetry)

        self.mock_audit_hub.log_anomaly.assert_called_once_with(source, severity, details, telemetry)
        self.assertEqual(result, expected_result)

    def test_aggregate_and_report(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        value = round(random.uniform(0.0, 1000.0), 2)

        expected_result = {"status": uuid.uuid4().hex}
        self.mock_audit_hub.aggregate_and_report.return_value = expected_result

        result = self.pipeline.aggregate_and_report(metric_name, value)

        self.mock_audit_hub.aggregate_and_report.assert_called_once_with(metric_name, value)
        self.assertEqual(result, expected_result)

    def test_run_audit_and_export_json(self):
        output_path = f"/reports/{uuid.uuid4().hex[:8]}.json"
        expected_path = f"/reports/generated_{uuid.uuid4().hex[:8]}.json"
        self.mock_exporter.export_json_report.return_value = expected_path

        result = self.pipeline.run_audit_and_export_json(output_path)

        self.mock_audit_hub.generate_final_report.assert_called_once()
        self.mock_exporter.export_json_report.assert_called_once_with(output_path)
        self.assertEqual(result, expected_path)

    def test_run_audit_and_export_json_error(self):
        output_path = f"/reports/{uuid.uuid4().hex[:8]}.json"
        error_message = f"Error_{uuid.uuid4().hex[:6]}"
        self.mock_exporter.export_json_report.side_effect = Exception(error_message)

        with self.assertRaises(DigestAuditPipelineError) as ctx:
            self.pipeline.run_audit_and_export_json(output_path)

        self.assertIn(error_message, str(ctx.exception))

    def test_run_audit_and_export_html(self):
        output_path = f"/reports/{uuid.uuid4().hex[:8]}.html"
        expected_path = f"/reports/generated_{uuid.uuid4().hex[:8]}.html"
        self.mock_exporter.export_html_report.return_value = expected_path

        result = self.pipeline.run_audit_and_export_html(output_path)

        self.mock_audit_hub.generate_final_report.assert_called_once()
        self.mock_exporter.export_html_report.assert_called_once_with(output_path)
        self.assertEqual(result, expected_path)

    def test_run_audit_and_export_html_error(self):
        output_path = f"/reports/{uuid.uuid4().hex[:8]}.html"
        error_message = f"Error_{uuid.uuid4().hex[:6]}"
        self.mock_audit_hub.generate_final_report.side_effect = Exception(error_message)

        with self.assertRaises(DigestAuditPipelineError) as ctx:
            self.pipeline.run_audit_and_export_html(output_path)

        self.assertIn(error_message, str(ctx.exception))

    def test_run_audit_and_export_dispatcher_html(self):
        output_path = f"/reports/{uuid.uuid4().hex[:8]}.html"
        expected_path = f"/reports/generated_{uuid.uuid4().hex[:8]}.html"
        self.mock_exporter.export_html_report.return_value = expected_path

        result = self.pipeline.run_audit_and_export(output_path)

        self.mock_audit_hub.generate_final_report.assert_called_once()
        self.mock_exporter.export_html_report.assert_called_once_with(output_path)
        self.mock_exporter.export_json_report.assert_not_called()
        self.assertEqual(result, expected_path)

    def test_run_audit_and_export_dispatcher_json(self):
        ext = random.choice([".json", ".txt", ".xml", ""])
        output_path = f"/reports/{uuid.uuid4().hex[:8]}{ext}"
        expected_path = f"/reports/generated_{uuid.uuid4().hex[:8]}{ext}"
        self.mock_exporter.export_json_report.return_value = expected_path

        result = self.pipeline.run_audit_and_export(output_path)

        self.mock_audit_hub.generate_final_report.assert_called_once()
        self.mock_exporter.export_json_report.assert_called_once_with(output_path)
        self.mock_exporter.export_html_report.assert_not_called()
        self.assertEqual(result, expected_path)

    def test_run_audit_and_export_dispatcher_error(self):
        output_path = f"/reports/{uuid.uuid4().hex[:8]}.json"
        error_message = f"Fatal_{uuid.uuid4().hex[:6]}"
        self.mock_exporter.export_json_report.side_effect = RuntimeError(error_message)

        with self.assertRaises(DigestAuditPipelineError) as ctx:
            self.pipeline.run_audit_and_export(output_path)

        self.assertIn(error_message, str(ctx.exception))