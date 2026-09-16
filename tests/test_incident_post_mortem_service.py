import io
import random
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.incident_post_mortem_service import IncidentPostMortemService


class TestIncidentPostMortemService(unittest.TestCase):
    def setUp(self):
        self.service = IncidentPostMortemService()

    def test_fetch_incident_metrics_success(self):
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(100, 999)
        incident_id = uuid.uuid4().hex

        with patch.object(self.service.incident_aggregator, "aggregate", return_value={rand_key: rand_val}) as mock_aggregate:
            metrics = self.service._fetch_incident_metrics(incident_id)
            mock_aggregate.assert_called_once_with(incident_id)
            self.assertEqual(metrics.get(rand_key), rand_val)

    def test_fetch_incident_metrics_invalid_type(self):
        incident_id = uuid.uuid4().hex
        rand_str = uuid.uuid4().hex

        with patch.object(self.service.incident_aggregator, "aggregate", return_value=rand_str):
            metrics = self.service._fetch_incident_metrics(incident_id)
            self.assertEqual(metrics, {})

    def test_fetch_recovery_logs_bytes(self):
        incident_id = uuid.uuid4().hex
        rand_text = uuid.uuid4().hex
        raw_bytes = rand_text.encode('utf-8')

        with patch.object(self.service.error_recovery_hub, "get_logs", return_value=raw_bytes):
            stream = self.service._fetch_recovery_logs(incident_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), raw_bytes)

    def test_fetch_recovery_logs_string(self):
        incident_id = uuid.uuid4().hex
        rand_text = uuid.uuid4().hex

        with patch.object(self.service.error_recovery_hub, "get_logs", return_value=rand_text):
            stream = self.service._fetch_recovery_logs(incident_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read().decode('utf-8'), rand_text)

    def test_fetch_recovery_logs_fallback(self):
        incident_id = uuid.uuid4().hex
        rand_num = random.randint(1, 100)

        with patch.object(self.service.error_recovery_hub, "get_logs", return_value=rand_num):
            stream = self.service._fetch_recovery_logs(incident_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), b"")

    def test_parse_recovery_logs(self):
        line1 = uuid.uuid4().hex
        line2 = uuid.uuid4().hex
        content = f"   {line1}   \n\n   {line2}   ".encode('utf-8')
        stream = io.BytesIO(content)

        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [line1, line2])

    def test_parse_recovery_logs_empty(self):
        stream = io.BytesIO(b"")
        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [])

    def test_evaluate_root_cause_complex(self):
        timeout_val = random.randint(5, 50)
        metrics = {
            "memory_leak_detected": True,
            "timeout_count": timeout_val
        }
        log_line = uuid.uuid4().hex
        logs = [log_line]

        cause = self.service._evaluate_root_cause(metrics, logs)
        self.assertIn("Memory leak detected", cause)
        self.assertIn(f"High timeout count: {timeout_val}", cause)
        self.assertIn(log_line, cause)

    def test_generate_report_with_dict_incident(self):
        incident_id = uuid.uuid4().hex
        error_code = uuid.uuid4().hex[:8]
        memory_mb = random.randint(500, 2048)
        log_content = uuid.uuid4().hex

        incident_data = {
            "incident_id": incident_id,
            "error_code": error_code,
            "metrics": {
                "memory_leak_mb": memory_mb
            }
        }
        recovery_data = {
            "logs": log_content.encode('utf-8')
        }

        with patch.object(self.service.report_exporter, "export") as mock_export:
            report = self.service.generate_report(incident_data, recovery_data)
            self.assertEqual(report["incident_id"], incident_id)
            self.assertIn(error_code, report["root_cause_analysis"])
            self.assertIn("Memory leak detected", report["root_cause_analysis"])
            self.assertEqual(report["metrics_snapshot"]["memory_leak_mb"], memory_mb)
            self.assertEqual(report["recovery_logs_summary"], log_content)
            mock_export.assert_called_once_with(report)

    def test_generate_report_with_str_incident(self):
        incident_id = uuid.uuid4().hex
        metric_key = uuid.uuid4().hex
        metric_val = random.randint(10, 500)
        log_line = uuid.uuid4().hex

        with patch.object(self.service, "_fetch_incident_metrics", return_value={metric_key: metric_val}) as mock_metrics, \
             patch.object(self.service, "_fetch_recovery_logs", return_value=io.BytesIO(log_line.encode('utf-8'))) as mock_logs, \
             patch.object(self.service.report_exporter, "export") as mock_export:

            report = self.service.generate_report(incident_id)

            mock_metrics.assert_called_once_with(incident_id)
            mock_logs.assert_called_once_with(incident_id)
            self.assertEqual(report["incident_id"], incident_id)
            self.assertEqual(report["metrics_snapshot"][metric_key], metric_val)
            self.assertIn(log_line, report["recovery_logs_summary"])
            mock_export.assert_called_once_with(report)


if __name__ == '__main__':
    unittest.main()