import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.audit_report_exporter import (
    AuditReportExporter,
    AuditReportExporterError
)


class TestAuditReportExporter(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/repo_{uuid.uuid4().hex}"
        self.rand_log = f"/tmp/log_{uuid.uuid4().hex}"
        self.rand_threshold = round(random.uniform(0.1, 0.9), 2)

        self.mock_hub = MagicMock()
        self.mock_digest = MagicMock()

        self.exporter = AuditReportExporter(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold,
            anomaly_audit_hub=self.mock_hub,
            digest_exporter=self.mock_digest
        )

    def test_init_creates_default_components(self):
        with patch('skills.audit_report_exporter.AnomalyAuditHub') as mock_ah_class, \
             patch('skills.audit_report_exporter.DigestExporter') as mock_de_class:

            exp = AuditReportExporter(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )

            mock_ah_class.assert_called_once_with(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )
            mock_de_class.assert_called_once()
            self.assertIsNotNone(exp.anomaly_audit_hub)
            self.assertIsNotNone(exp.digest_exporter)

    def test_export_json_report_success(self):
        output_file = f"/tmp/report_{uuid.uuid4().hex}.json"
        expected_result = f"/path/to/exported_{uuid.uuid4().hex}.json"
        self.mock_digest.export_json_report.return_value = expected_result

        res = self.exporter.export_json_report(output_file)

        self.assertEqual(res, expected_result)
        self.mock_digest.export_json_report.assert_called_once_with(output_file)

    def test_export_json_report_failure_raises_custom_error(self):
        output_file = f"/tmp/fail_{uuid.uuid4().hex}.json"
        rand_err_msg = f"err_{uuid.uuid4().hex}"
        self.mock_digest.export_json_report.side_effect = Exception(rand_err_msg)

        with self.assertRaises(AuditReportExporterError) as ctx:
            self.exporter.export_json_report(output_file)

        self.assertIn(rand_err_msg, str(ctx.exception))

    def test_export_html_report_success(self):
        output_file = f"/tmp/report_{uuid.uuid4().hex}.html"
        expected_result = f"/path/to/exported_{uuid.uuid4().hex}.html"
        self.mock_digest.export_html_report.return_value = expected_result

        res = self.exporter.export_html_report(output_file)

        self.assertEqual(res, expected_result)
        self.mock_digest.export_html_report.assert_called_once_with(output_file)

    def test_export_html_report_failure_raises_custom_error(self):
        output_file = f"/tmp/fail_{uuid.uuid4().hex}.html"
        rand_err_msg = f"err_{uuid.uuid4().hex}"
        self.mock_digest.export_html_report.side_effect = Exception(rand_err_msg)

        with self.assertRaises(AuditReportExporterError) as ctx:
            self.exporter.export_html_report(output_file)

        self.assertIn(rand_err_msg, str(ctx.exception))

    def test_aggregate_and_report(self):
        metric_name = f"metric_{uuid.uuid4().hex}"
        metric_value = random.randint(1, 1000)
        expected_agg_result = f"res_{uuid.uuid4().hex}"
        self.mock_hub.aggregate_and_report.return_value = expected_agg_result

        res = self.exporter.aggregate_and_report(metric_name, metric_value)

        self.assertEqual(res, expected_agg_result)
        self.mock_hub.aggregate_and_report.assert_called_once_with(metric_name, metric_value)

    def test_log_anomaly(self):
        source = f"src_{uuid.uuid4().hex}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {"info": uuid.uuid4().hex}
        telemetry = {"cpu": random.random()}
        expected_log_result = f"logged_{uuid.uuid4().hex}"
        self.mock_hub.log_anomaly.return_value = expected_log_result

        res = self.exporter.log_anomaly(source, severity, details, telemetry)

        self.assertEqual(res, expected_log_result)
        self.mock_hub.log_anomaly.assert_called_once_with(source, severity, details, telemetry)

    def test_export_stream_to_json(self):
        stream_id = uuid.uuid4().hex
        output_file = f"/tmp/stream_{uuid.uuid4().hex}.json"
        expected_result = f"/path/to/stream_{uuid.uuid4().hex}.json"
        self.mock_digest.export_stream_to_json.return_value = expected_result

        res = self.exporter.export_stream_to_json(stream_id, output_file)

        self.assertEqual(res, expected_result)
        self.mock_digest.export_stream_to_json.assert_called_once_with(stream_id, output_file)

    def test_export_to_json_with_preferred_method(self):
        output_file = f"/tmp/pref_{uuid.uuid4().hex}.json"
        expected_result = f"/path/pref_{uuid.uuid4().hex}.json"

        self.mock_digest.export_to_json = MagicMock(return_value=expected_result)

        res = self.exporter.export_to_json(output_file)

        self.assertEqual(res, expected_result)
        self.mock_digest.export_to_json.assert_called_once_with(output_file)

    def test_export_to_json_fallback_to_json_report(self):
        output_file = f"/tmp/fallback_{uuid.uuid4().hex}.json"
        expected_result = f"/path/fallback_{uuid.uuid4().hex}.json"

        if hasattr(self.mock_digest, 'export_to_json'):
            del self.mock_digest.export_to_json

        self.mock_digest.export_json_report.return_value = expected_result

        res = self.exporter.export_to_json(output_file)

        self.assertEqual(res, expected_result)
        self.mock_digest.export_json_report.assert_called_once_with(output_file)

    def test_export_to_json_failure_raises_custom_error(self):
        output_file = f"/tmp/fail_json_{uuid.uuid4().hex}.json"
        rand_err_msg = f"err_{uuid.uuid4().hex}"

        self.mock_digest.export_to_json = MagicMock(side_effect=Exception(rand_err_msg))

        with self.assertRaises(AuditReportExporterError) as ctx:
            self.exporter.export_to_json(output_file)

        self.assertIn(rand_err_msg, str(ctx.exception))

    def test_io_stream_compatibility(self):
        stream_id = uuid.uuid4().hex
        output_stream = io.BytesIO(b"dummy payload")
        expected_path = f"/tmp/out_{uuid.uuid4().hex}"
        self.mock_digest.export_stream_to_json.return_value = expected_path

        res = self.exporter.export_stream_to_json(stream_id, output_stream)
        self.assertEqual(res, expected_path)
        self.mock_digest.export_stream_to_json.assert_called_once_with(stream_id, output_stream)