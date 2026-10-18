import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.audit_exporter import AuditExporter
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestAuditExporter(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/repo/{uuid.uuid4().hex}"
        self.rand_log = f"/log/{uuid.uuid4().hex}.log"
        self.rand_threshold = round(random.uniform(1.0, 100.0), 2)

        self.exporter_instance = AuditExporter(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

    def test_initialization(self):
        self.assertIsInstance(self.exporter_instance.audit_hub, AnomalyAuditHub)
        self.assertIsInstance(self.exporter_instance.digest_exporter, DigestExporter)
        self.assertEqual(self.exporter_instance.audit_hub.threshold, self.rand_threshold)

    @patch('skills.audit_exporter.DigestExporter.export_to_json')
    def test_export_audit_json_success(self, mock_export_json):
        expected_path = f"/output/{uuid.uuid4().hex}.json"
        mock_export_json.return_value = expected_path

        result = self.exporter_instance.export_audit_json(expected_path)

        mock_export_json.assert_called_once_with(expected_path)
        self.assertEqual(result, expected_path)

    @patch('skills.audit_exporter.DigestExporter.export_to_html')
    def test_export_audit_html_success(self, mock_export_html):
        expected_path = f"/output/{uuid.uuid4().hex}.html"
        mock_export_html.return_value = expected_path

        result = self.exporter_instance.export_audit_html(expected_path)

        mock_export_html.assert_called_once_with(expected_path)
        self.assertEqual(result, expected_path)

    @patch('skills.audit_exporter.DigestExporter.export_to_json')
    def test_export_audit_json_error(self, mock_export_json):
        error_message = f"err_{uuid.uuid4().hex}"
        mock_export_json.side_effect = DigestExporterError(error_message)
        bad_path = f"/bad/path/{uuid.uuid4().hex}.json"

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter_instance.export_audit_json(bad_path)

        self.assertIn(error_message, str(ctx.exception))

    def test_log_and_export_flow(self):
        source_name = f"source_{uuid.uuid4().hex[:6]}"
        severity_level = random.choice(["INFO", "WARN", "CRITICAL"])
        details_text = f"details_{uuid.uuid4().hex}"
        telemetry_data = {uuid.uuid4().hex: random.randint(1, 1000)}
        output_file = f"/tmp/{uuid.uuid4().hex}.json"

        with patch('skills.audit_exporter.DigestExporter.export_to_json') as mock_json:
            mock_json.return_value = output_file

            self.exporter_instance.audit_hub.log_anomaly(
                source=source_name,
                severity=severity_level,
                details=details_text,
                telemetry_snapshot=telemetry_data
            )

            res = self.exporter_instance.export_audit_json(output_file)

            self.assertEqual(res, output_file)
            mock_json.assert_called_once_with(output_file)

    def test_stream_export_handler(self):
        stream_id = uuid.uuid4().hex
        output_file = f"/stream/out_{uuid.uuid4().hex}.json"

        with patch('skills.audit_exporter.DigestExporter.export_stream_to_json') as mock_stream:
            mock_stream.return_value = output_file

            result = self.exporter_instance.export_stream(stream_id, output_file)

            mock_stream.assert_called_once_with(stream_id, output_file)
            self.assertEqual(result, output_file)


if __name__ == '__main__':
    unittest.main()