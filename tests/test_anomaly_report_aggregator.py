import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.anomaly_report_aggregator import AnomalyReportAggregator
from skills.anomaly_logger import AnomalyLogger
from skills.digest_exporter import DigestExporter, DigestExporterError

class TestAnomalyReportAggregator(unittest.TestCase):

    def setUp(self):
        self.rand_log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.rand_output_path = f"/tmp/{uuid.uuid4().hex}_report.json"
        self.rand_html_path = f"/tmp/{uuid.uuid4().hex}_report.html"
        self.rand_source = ''.join(random.choices(string.ascii_letters, k=8))
        self.rand_severity = random.choice(['INFO', 'WARNING', 'CRITICAL', 'FATAL'])
        self.rand_details = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        self.rand_telemetry = {"cpu": random.uniform(10.0, 99.9), "mem": random.randint(1024, 8192)}

    @patch('skills.anomaly_report_aggregator.AnomalyLogger')
    @patch('skills.anomaly_report_aggregator.DigestExporter')
    def test_aggregator_initialization_and_logging(self, mock_exporter_cls, mock_logger_cls):
        mock_logger_instance = mock_logger_cls.return_value
        mock_exporter_instance = mock_exporter_cls.return_value

        aggregator = AnomalyReportAggregator(log_path=self.rand_log_path)

        mock_logger_cls.assert_called_once_with(log_path=self.rand_log_path)
        self.assertIsNotNone(aggregator)

        aggregator.log_new_anomaly(
            source=self.rand_source,
            severity=self.rand_severity,
            details=self.rand_details,
            telemetry_snapshot=self.rand_telemetry
        )

        mock_logger_instance.log_anomaly.assert_called_once_with(
            self.rand_source,
            self.rand_severity,
            self.rand_details,
            self.rand_telemetry
        )

    @patch('skills.anomaly_report_aggregator.AnomalyLogger')
    @patch('skills.anomaly_report_aggregator.DigestExporter')
    def test_export_json_digest_success(self, mock_exporter_cls, mock_logger_cls):
        mock_logger_instance = mock_logger_cls.return_value
        mock_exporter_instance = mock_exporter_cls.return_value

        expected_export_result = f"/exports/{uuid.uuid4().hex}.json"
        mock_exporter_instance.export_json_report.return_value = expected_export_result

        aggregator = AnomalyReportAggregator(log_path=self.rand_log_path)
        result = aggregator.generate_json_digest(output_path=self.rand_output_path)

        mock_exporter_instance.export_json_report.assert_called_once_with(self.rand_output_path)
        self.assertEqual(result, expected_export_result)

    @patch('skills.anomaly_report_aggregator.AnomalyLogger')
    @patch('skills.anomaly_report_aggregator.DigestExporter')
    def test_export_html_digest_success(self, mock_exporter_cls, mock_logger_cls):
        mock_logger_instance = mock_logger_cls.return_value
        mock_exporter_instance = mock_exporter_cls.return_value

        expected_export_result = f"/exports/{uuid.uuid4().hex}.html"
        mock_exporter_instance.export_html_report.return_value = expected_export_result

        aggregator = AnomalyReportAggregator(log_path=self.rand_log_path)
        result = aggregator.generate_html_digest(output_path=self.rand_html_path)

        mock_exporter_instance.export_html_report.assert_called_once_with(self.rand_html_path)
        self.assertEqual(result, expected_export_result)

    @patch('skills.anomaly_report_aggregator.AnomalyLogger')
    @patch('skills.anomaly_report_aggregator.DigestExporter')
    def test_export_digest_raises_error(self, mock_exporter_cls, mock_logger_cls):
        mock_logger_instance = mock_logger_cls.return_value
        mock_exporter_instance = mock_exporter_cls.return_value

        rand_error_msg = f"Export failed due to {uuid.uuid4().hex}"
        mock_exporter_instance.export_json_report.side_effect = DigestExporterError(rand_error_msg)

        aggregator = AnomalyReportAggregator(log_path=self.rand_log_path)

        with self.assertRaises(DigestExporterError) as ctx:
            aggregator.generate_json_digest(output_path=self.rand_output_path)

        self.assertIn(rand_error_msg, str(ctx.exception))

    @patch('skills.anomaly_report_aggregator.AnomalyLogger')
    @patch('skills.anomaly_report_aggregator.DigestExporter')
    def test_get_structured_summary(self, mock_exporter_cls, mock_logger_cls):
        mock_logger_instance = mock_logger_cls.return_value

        rand_structured_data = {
            "total_anomalies": random.randint(1, 100),
            "signature": uuid.uuid4().hex
        }
        mock_logger_instance.get_structured_report.return_value = rand_structured_data

        aggregator = AnomalyReportAggregator(log_path=self.rand_log_path)
        summary = aggregator.get_summary()

        mock_logger_instance.get_structured_report.assert_called_once()
        self.assertEqual(summary, rand_structured_data)
        self.assertEqual(summary["signature"], rand_structured_data["signature"])

    @patch('skills.anomaly_report_aggregator.AnomalyLogger')
    @patch('skills.anomaly_report_aggregator.DigestExporter')
    def test_clear_all_logs(self, mock_exporter_cls, mock_logger_cls):
        mock_logger_instance = mock_logger_cls.return_value

        aggregator = AnomalyReportAggregator(log_path=self.rand_log_path)
        aggregator.purge_logs()

        mock_logger_instance.clear_logs.assert_called_once()

if __name__ == '__main__':
    unittest.main()