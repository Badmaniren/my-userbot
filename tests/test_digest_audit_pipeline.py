import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.digest_audit_pipeline import DigestAuditPipeline, DigestAuditPipelineError


class TestDigestAuditPipeline(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = f"/repo/{uuid.uuid4().hex}"
        self.log_path_val = f"/logs/{uuid.uuid4().hex}.log"
        self.threshold_val = random.uniform(1.0, 100.0)
        self.output_json_val = f"/out/{uuid.uuid4().hex}.json"
        self.output_html_val = f"/out/{uuid.uuid4().hex}.html"

    def test_pipeline_initialization_default(self):
        with patch("skills.digest_audit_pipeline.AnomalyAuditHub") as mock_hub_cls, \
             patch("skills.digest_audit_pipeline.DigestExporter") as mock_exporter_cls:

            mock_hub_instance = MagicMock()
            mock_hub_cls.return_value = mock_hub_instance

            pipeline = DigestAuditPipeline(
                repo_path=self.repo_path_val,
                log_path=self.log_path_val,
                threshold=self.threshold_val,
                output_json_path=self.output_json_val,
                output_html_path=self.output_html_val
            )

            mock_hub_cls.assert_called_once_with(
                repo_path=self.repo_path_val,
                log_path=self.log_path_val,
                threshold=self.threshold_val
            )
            mock_exporter_cls.assert_called_once_with(mock_hub_instance)
            self.assertEqual(pipeline.output_json_path, self.output_json_val)
            self.assertEqual(pipeline.output_html_path, self.output_html_val)

    def test_pipeline_initialization_with_custom_audit_hub(self):
        custom_hub = MagicMock()
        with patch("skills.digest_audit_pipeline.DigestExporter") as mock_exporter_cls:
            pipeline = DigestAuditPipeline(
                audit_hub=custom_hub,
                output_json_path=self.output_json_val,
                output_html_path=self.output_html_val
            )

            self.assertEqual(pipeline.audit_hub, custom_hub)
            mock_exporter_cls.assert_called_once_with(custom_hub)
            self.assertEqual(pipeline.audit_hub.repo_path, None)
            self.assertEqual(pipeline.audit_hub.log_path, None)
            self.assertEqual(pipeline.audit_hub.threshold, None)

    def test_run_audit_and_export_json_success(self):
        custom_hub = MagicMock()
        expected_result = uuid.uuid4().hex

        with patch("skills.digest_audit_pipeline.DigestExporter") as mock_exporter_cls:
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.export_json_report.return_value = expected_result
            mock_exporter_cls.return_value = mock_exporter_instance

            pipeline = DigestAuditPipeline(
                audit_hub=custom_hub,
                output_json_path=self.output_json_val
            )

            source_val = ''.join(random.choices(string.ascii_letters, k=8))
            severity_val = random.choice(["INFO", "WARNING", "CRITICAL"])
            details_val = uuid.uuid4().hex
            metric_name_val = uuid.uuid4().hex
            metric_val = random.randint(1, 500)

            res = pipeline.run_audit_and_export_json(
                output_path=self.output_json_val,
                source=source_val,
                severity=severity_val,
                details=details_val,
                metric_name=metric_name_val,
                metric_value=metric_val
            )

            custom_hub.log_anomaly.assert_called_once_with(source_val, severity_val, details_val, None)
            custom_hub.aggregate_and_report.assert_called_once_with(metric_name_val, metric_val)
            custom_hub.generate_final_report.assert_called_once()
            mock_exporter_instance.export_json_report.assert_called_once_with(self.output_json_val)
            self.assertEqual(res, expected_result)

    def test_run_audit_and_export_html_success(self):
        custom_hub = MagicMock()
        expected_result = uuid.uuid4().hex

        with patch("skills.digest_audit_pipeline.DigestExporter") as mock_exporter_cls:
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.export_html_report.return_value = expected_result
            mock_exporter_cls.return_value = mock_exporter_instance

            pipeline = DigestAuditPipeline(
                audit_hub=custom_hub,
                output_html_path=self.output_html_val
            )

            source_val = ''.join(random.choices(string.ascii_letters, k=6))
            severity_val = random.choice(["ERROR", "DEBUG"])
            details_val = uuid.uuid4().hex

            res = pipeline.run_audit_and_export_html(
                output_path=self.output_html_val,
                source=source_val,
                severity=severity_val,
                details=details_val
            )

            custom_hub.log_anomaly.assert_called_once_with(source_val, severity_val, details_val, None)
            custom_hub.generate_final_report.assert_called_once()
            mock_exporter_instance.export_html_report.assert_called_once_with(self.output_html_val)
            self.assertEqual(res, expected_result)

    def test_run_export_pipeline_success(self):
        custom_hub = MagicMock()
        json_res = uuid.uuid4().hex
        html_res = uuid.uuid4().hex

        with patch("skills.digest_audit_pipeline.DigestExporter") as mock_exporter_cls:
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.export_json_report.return_value = json_res
            mock_exporter_instance.export_html_report.return_value = html_res
            mock_exporter_cls.return_value = mock_exporter_instance

            pipeline = DigestAuditPipeline(
                audit_hub=custom_hub,
                output_json_path=self.output_json_val,
                output_html_path=self.output_html_val
            )

            j_out, h_out = pipeline.run_export_pipeline()

            custom_hub.generate_final_report.assert_called_once()
            mock_exporter_instance.export_json_report.assert_called_once_with(self.output_json_val)
            mock_exporter_instance.export_html_report.assert_called_once_with(self.output_html_val)
            self.assertEqual(j_out, json_res)
            self.assertEqual(h_out, html_res)

    def test_aggregate_and_report_attribute_error_fallback(self):
        custom_hub = MagicMock()
        custom_hub.aggregate_and_report.side_effect = AttributeError("No method")

        aggregator_mock = MagicMock()
        custom_hub.aggregator = aggregator_mock

        with patch("skills.digest_audit_pipeline.DigestExporter"):
            pipeline = DigestAuditPipeline(audit_hub=custom_hub, output_json_path=self.output_json_val)

            metric_name_val = uuid.uuid4().hex
            metric_val = random.randint(10, 100)
            source_val = uuid.uuid4().hex
            severity_val = "INFO"
            details_val = uuid.uuid4().hex

            pipeline.run_audit_and_export_json(
                source=source_val,
                severity=severity_val,
                details=details_val,
                metric_name=metric_name_val,
                metric_value=metric_val
            )

            aggregator_mock.aggregate_and_report.assert_called_once_with(
                {"source": source_val, "severity": severity_val, "details": details_val},
                metric_name_val,
                metric_val
            )

    def test_pipeline_raises_digest_audit_pipeline_error(self):
        custom_hub = MagicMock()
        custom_hub.generate_final_report.side_effect = RuntimeError(uuid.uuid4().hex)

        with patch("skills.digest_audit_pipeline.DigestExporter"):
            pipeline = DigestAuditPipeline(audit_hub=custom_hub, output_json_path=self.output_json_val)

            with self.assertRaises(DigestAuditPipelineError):
                pipeline.run_audit_and_export_json()