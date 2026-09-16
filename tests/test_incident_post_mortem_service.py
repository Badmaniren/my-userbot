import io
import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.incident_post_mortem_service import IncidentPostMortemService


class TestIncidentPostMortemService(unittest.TestCase):

    def setUp(self):
        self.service = IncidentPostMortemService()

    def test_fetch_incident_metrics_success(self):
        rand_id = uuid.uuid4().hex
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(100, 999)
        expected_dict = {rand_key: rand_val}

        with patch.object(self.service.incident_aggregator, 'aggregate', return_value=expected_dict) as mock_agg:
            result = self.service._fetch_incident_metrics(rand_id)
            mock_agg.assert_called_once_with(rand_id)
            self.assertEqual(result, expected_dict)

    def test_fetch_incident_metrics_invalid_type(self):
        rand_id = uuid.uuid4().hex
        rand_invalid = random.choice([uuid.uuid4().hex, random.randint(1, 100), None])

        with patch.object(self.service.incident_aggregator, 'aggregate', return_value=rand_invalid):
            result = self.service._fetch_incident_metrics(rand_id)
            self.assertEqual(result, {})

    def test_fetch_recovery_logs_bytes(self):
        rand_id = uuid.uuid4().hex
        rand_content = "".join(random.choices(string.ascii_letters + string.digits, k=25))
        byte_data = rand_content.encode('utf-8')

        with patch.object(self.service.error_recovery_hub, 'get_logs', return_value=byte_data):
            stream = self.service._fetch_recovery_logs(rand_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), byte_data)

    def test_fetch_recovery_logs_string(self):
        rand_id = uuid.uuid4().hex
        rand_content = "".join(random.choices(string.ascii_letters + string.digits, k=30))

        with patch.object(self.service.error_recovery_hub, 'get_logs', return_value=rand_content):
            stream = self.service._fetch_recovery_logs(rand_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read().decode('utf-8'), rand_content)

    def test_fetch_recovery_logs_unsupported_type(self):
        rand_id = uuid.uuid4().hex
        rand_invalid = random.randint(1000, 9999)

        with patch.object(self.service.error_recovery_hub, 'get_logs', return_value=rand_invalid):
            stream = self.service._fetch_recovery_logs(rand_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), b"")

    def test_parse_recovery_logs_valid_stream(self):
        line1 = "".join(random.choices(string.ascii_lowercase, k=10))
        line2 = "".join(random.choices(string.ascii_lowercase, k=12))
        content = f"\n  {line1}  \n\n{line2}\n"
        stream = io.BytesIO(content.encode('utf-8'))

        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [line1, line2])

    def test_parse_recovery_logs_empty_stream(self):
        stream = io.BytesIO(b"")
        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [])

    def test_evaluate_root_cause_memory_and_timeout(self):
        rand_mb = random.randint(128, 4096)
        rand_timeouts = random.randint(1, 50)
        rand_log = "".join(random.choices(string.ascii_letters, k=15))

        metrics = {
            "memory_leak_detected": True,
            "memory_leak_mb": rand_mb,
            "timeout_count": rand_timeouts
        }
        logs = [rand_log]

        cause = self.service._evaluate_root_cause(metrics, logs)
        self.assertIn("Memory leak detected", cause)
        self.assertIn(f"High timeout count: {rand_timeouts}", cause)
        self.assertIn(rand_log, cause)

    def test_generate_report_with_dict_incident(self):
        rand_inc_id = uuid.uuid4().hex
        rand_err_code = f"ERR-{random.randint(100, 999)}"
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(1, 100)
        rand_log_line = "".join(random.choices(string.ascii_letters, k=20))

        incident_dict = {
            "incident_id": rand_inc_id,
            "error_code": rand_err_code,
            "metrics": {rand_metric_key: rand_metric_val}
        }
        recovery_data = {
            "logs": rand_log_line.encode('utf-8')
        }

        with patch.object(self.service.report_exporter, 'export') as mock_export:
            report = self.service.generate_report(incident_dict, recovery_data)
            
            self.assertEqual(report["incident_id"], rand_inc_id)
            self.assertIn(rand_err_code, report["root_cause_analysis"])
            self.assertEqual(report["metrics_snapshot"][rand_metric_key], rand_metric_val)
            self.assertEqual(report["recovery_logs_summary"], rand_log_line)
            mock_export.assert_called_once_with(report)

    def test_generate_report_with_string_incident(self):
        rand_inc_id = uuid.uuid4().hex
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(500, 999)
        rand_log_bytes = "".join(random.choices(string.ascii_letters, k=15)).encode('utf-8')

        with patch.object(self.service, '_fetch_incident_metrics', return_value={rand_metric_key: rand_metric_val}) as mock_metrics, \
             patch.object(self.service, '_fetch_recovery_logs', return_value=io.BytesIO(rand_log_bytes)) as mock_logs, \
             patch.object(self.service.report_exporter, 'export') as mock_export:

            report = self.service.generate_report(rand_inc_id)

            mock_metrics.assert_called_once_with(rand_inc_id)
            mock_logs.assert_called_once_with(rand_inc_id)
            self.assertEqual(report["incident_id"], rand_inc_id)
            self.assertEqual(report["metrics_snapshot"][rand_metric_key], rand_metric_val)
            self.assertEqual(report["recovery_logs_summary"], rand_log_bytes.decode('utf-8'))
            mock_export.assert_called_once_with(report)

    def test_import_historical_data(self):
        rand_id_1 = uuid.uuid4().hex
        rand_id_2 = uuid.uuid4().hex
        batch = [
            {"incident_id": rand_id_1, "metrics": {}},
            {"incident_id": rand_id_2, "metrics": {}}
        ]

        with patch.object(self.service, 'generate_report', side_effect=lambda inc: {"incident_id": inc["incident_id"], "mocked": True}) as mock_gen:
            reports = self.service.import_historical_data(batch)
            self.assertEqual(len(reports), 2)
            self.assertEqual(reports[0]["incident_id"], rand_id_1)
            self.assertEqual(reports[1]["incident_id"], rand_id_2)
            self.assertEqual(mock_gen.call_count, 2)

    def test_export_summary_analytics(self):
        rand_id = uuid.uuid4().hex
        incidents = [rand_id]
        rand_report_id = uuid.uuid4().hex

        with patch.object(self.service, 'generate_report', return_value={"report_id": rand_report_id}) as mock_gen:
            summary = self.service.export_summary_analytics(incidents)

            self.assertEqual(summary["total_incidents"], 1)
            self.assertEqual(len(summary["reports_summary"]), 1)
            self.assertEqual(summary["reports_summary"][0]["report_id"], rand_report_id)
            mock_gen.assert_called_once_with(rand_id)


if __name__ == '__main__':
    unittest.main()