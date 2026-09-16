import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
import string

from skills.incident_post_mortem_service import IncidentPostMortemService


class TestIncidentPostMortemService(unittest.TestCase):

    def setUp(self):
        self.service = IncidentPostMortemService()

    def test_fetch_incident_metrics_valid(self):
        rand_id = uuid.uuid4().hex
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(100, 999)

        with patch.object(self.service.incident_aggregator, "aggregate", return_value={rand_key: rand_val}) as mock_agg:
            metrics = self.service._fetch_incident_metrics(rand_id)
            mock_agg.assert_called_once_with(rand_id)
            self.assertEqual(metrics.get(rand_key), rand_val)

    def test_fetch_incident_metrics_invalid_type(self):
        rand_id = uuid.uuid4().hex
        rand_str = uuid.uuid4().hex

        with patch.object(self.service.incident_aggregator, "aggregate", return_value=rand_str):
            metrics = self.service._fetch_incident_metrics(rand_id)
            self.assertEqual(metrics, {})

    def test_fetch_incident_metrics_no_attribute(self):
        rand_id = uuid.uuid4().hex
        delattr(self.service.incident_aggregator, "aggregate")
        metrics = self.service._fetch_incident_metrics(rand_id)
        self.assertEqual(metrics, {})

    def test_fetch_recovery_logs_bytes(self):
        rand_id = uuid.uuid4().hex
        rand_log_data = uuid.uuid4().hex.encode('utf-8')

        with patch.object(self.service.error_recovery_hub, "get_logs", return_value=rand_log_data) as mock_logs:
            stream = self.service._fetch_recovery_logs(rand_id)
            mock_logs.assert_called_once_with(rand_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), rand_log_data)

    def test_fetch_recovery_logs_string(self):
        rand_id = uuid.uuid4().hex
        rand_log_str = uuid.uuid4().hex

        with patch.object(self.service.error_recovery_hub, "get_logs", return_value=rand_log_str):
            stream = self.service._fetch_recovery_logs(rand_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read().decode('utf-8'), rand_log_str)

    def test_fetch_recovery_logs_empty(self):
        rand_id = uuid.uuid4().hex

        with patch.object(self.service.error_recovery_hub, "get_logs", return_value=None):
            stream = self.service._fetch_recovery_logs(rand_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), b"")

    def test_parse_recovery_logs_valid(self):
        line1 = uuid.uuid4().hex
        line2 = uuid.uuid4().hex
        raw_content = f"  {line1} \n\n   {line2}  ".encode('utf-8')
        stream = io.BytesIO(raw_content)

        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [line1, line2])

    def test_parse_recovery_logs_empty(self):
        stream = io.BytesIO(b"")
        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [])

    def test_evaluate_root_cause_comprehensive(self):
        rand_timeout = random.randint(10, 100)
        rand_log = uuid.uuid4().hex

        metrics = {
            "memory_leak_detected": True,
            "timeout_count": rand_timeout
        }
        logs = [rand_log]

        result = self.service._evaluate_root_cause(metrics, logs)
        self.assertIn("Memory leak detected", result)
        self.assertIn(f"High timeout count: {rand_timeout}", result)
        self.assertIn(rand_log, result)

    def test_generate_report_with_dict_incident(self):
        rand_incident_id = uuid.uuid4().hex
        rand_error_code = f"ERR-{random.randint(1000, 9999)}"
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(1, 500)
        rand_log_line = uuid.uuid4().hex

        incident_dict = {
            "incident_id": rand_incident_id,
            "error_code": rand_error_code,
            "metrics": {
                rand_metric_key: rand_metric_val,
                "memory_leak_mb": random.randint(5, 50)
            }
        }
        recovery_data = {
            "logs": rand_log_line.encode('utf-8')
        }

        with patch.object(self.service.report_exporter, "export") as mock_export:
            report = self.service.generate_report(incident_dict, recovery_data)
            mock_export.assert_called_once()
            self.assertEqual(report["incident_id"], rand_incident_id)
            self.assertIn("Root cause identified", report["root_cause_analysis"])
            self.assertIn(rand_error_code, report["root_cause_analysis"])
            self.assertEqual(report["metrics_snapshot"][rand_metric_key], rand_metric_val)
            self.assertIn(rand_log_line, report["recovery_logs_summary"])

    def test_generate_report_with_string_incident(self):
        rand_incident_id = uuid.uuid4().hex
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(1000, 9999)
        rand_log_line = uuid.uuid4().hex

        with patch.object(self.service, "_fetch_incident_metrics", return_value={rand_metric_key: rand_metric_val}) as mock_metrics, \
             patch.object(self.service, "_fetch_recovery_logs", return_value=io.BytesIO(rand_log_line.encode('utf-8'))) as mock_logs, \
             patch.object(self.service.report_exporter, "export") as mock_export:

            report = self.service.generate_report(rand_incident_id)
            mock_metrics.assert_called_once_with(rand_incident_id)
            mock_logs.assert_called_once_with(rand_incident_id)
            mock_export.assert_called_once()

            self.assertEqual(report["incident_id"], rand_incident_id)
            self.assertEqual(report["metrics_snapshot"][rand_metric_key], rand_metric_val)
            self.assertIn(rand_log_line, report["recovery_logs_summary"])
            self.assertIn("Root cause identified", report["root_cause"])


if __name__ == '__main__':
    unittest.main()