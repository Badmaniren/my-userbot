import io
import uuid
import random
import string
import unittest
from unittest.mock import MagicMock, patch

from skills.incident_post_mortem_service import IncidentPostMortemService


class TestIncidentPostMortemService(unittest.TestCase):

    def setUp(self):
        self.service = IncidentPostMortemService()

    def _random_string(self, length=10):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for _ in range(length))

    def test_parse_recovery_logs_empty(self):
        empty_stream = io.BytesIO(b"")
        res = self.service._parse_recovery_logs(empty_stream)
        self.assertEqual(res, [])

    def test_parse_recovery_logs_valid_bytes(self):
        line1 = self._random_string(8)
        line2 = self._random_string(12)
        raw_data = f"\n  {line1}  \n\n{line2}\n".encode('utf-8')
        stream = io.BytesIO(raw_data)
        
        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [line1, line2])

    def test_fetch_incident_metrics_valid_dict(self):
        inc_id = uuid.uuid4().hex
        expected_metrics = {self._random_string(5): random.randint(1, 100)}
        
        with patch.object(self.service.incident_aggregator, 'aggregate', return_value=expected_metrics) as mock_agg:
            metrics = self.service._fetch_incident_metrics(inc_id)
            mock_agg.assert_called_once_with(inc_id)
            self.assertEqual(metrics, expected_metrics)

    def test_fetch_incident_metrics_invalid_type(self):
        inc_id = uuid.uuid4().hex
        with patch.object(self.service.incident_aggregator, 'aggregate', return_value=self._random_string()):
            metrics = self.service._fetch_incident_metrics(inc_id)
            self.assertEqual(metrics, {})

    def test_fetch_recovery_logs_bytes(self):
        inc_id = uuid.uuid4().hex
        random_bytes = self._random_string(15).encode('utf-8')
        
        with patch.object(self.service.error_recovery_hub, 'get_logs', return_value=random_bytes) as mock_logs:
            stream = self.service._fetch_recovery_logs(inc_id)
            mock_logs.assert_called_once_with(inc_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), random_bytes)

    def test_fetch_recovery_logs_string(self):
        inc_id = uuid.uuid4().hex
        random_str = self._random_string(20)
        
        with patch.object(self.service.error_recovery_hub, 'get_logs', return_value=random_str):
            stream = self.service._fetch_recovery_logs(inc_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read().decode('utf-8'), random_str)

    def test_fetch_recovery_logs_fallback(self):
        inc_id = uuid.uuid4().hex
        with patch.object(self.service.error_recovery_hub, 'get_logs', return_value=random.randint(1, 500)):
            stream = self.service._fetch_recovery_logs(inc_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), b"")

    def test_evaluate_root_cause_comprehensive(self):
        memory_leak_mb = random.randint(100, 2048)
        timeout_count = random.randint(1, 10)
        metrics = {
            "memory_leak_detected": True,
            "memory_leak_mb": memory_leak_mb,
            "timeout_count": timeout_count
        }
        log_line = self._random_string(10)
        logs = [log_line]

        result = self.service._evaluate_root_cause(metrics, logs)
        
        self.assertIn("Root cause identified.", result)
        self.assertIn("Memory leak detected", result)
        self.assertIn(f"High timeout count: {timeout_count}", result)
        self.assertIn(f"Logs analysis: {log_line}", result)

    def test_generate_report_with_dict_incident(self):
        inc_id = uuid.uuid4().hex
        error_code = f"ERR_{random.randint(1000, 9999)}"
        metric_key = self._random_string(6)
        metric_val = random.randint(10, 50)
        log_content = self._random_string(12)

        incident_payload = {
            "incident_id": inc_id,
            "metrics": {metric_key: metric_val},
            "error_code": error_code
        }
        recovery_data = {
            "logs": log_content.encode('utf-8')
        }

        with patch.object(self.service.report_exporter, 'export') as mock_export:
            report = self.service.generate_report(incident_payload, recovery_data)
            
            mock_export.assert_called_once()
            self.assertEqual(report["incident_id"], inc_id)
            self.assertEqual(report["metrics_snapshot"][metric_key], metric_val)
            self.assertIn(error_code, report["root_cause_analysis"])
            self.assertIn(log_content, report["recovery_logs_summary"])
            self.assertIsInstance(report["report_id"], str)

    def test_generate_report_with_string_incident(self):
        inc_id = uuid.uuid4().hex
        fetched_metrics = {self._random_string(4): random.randint(1, 5)}
        fetched_logs = self._random_string(15).encode('utf-8')

        with patch.object(self.service, '_fetch_incident_metrics', return_value=fetched_metrics) as mock_metrics, \
             patch.object(self.service, '_fetch_recovery_logs', return_value=io.BytesIO(fetched_logs)) as mock_logs, \
             patch.object(self.service.report_exporter, 'export') as mock_export:
            
            report = self.service.generate_report(inc_id)

            mock_metrics.assert_called_once_with(inc_id)
            mock_logs.assert_called_once_with(inc_id)
            mock_export.assert_called_once()

            self.assertEqual(report["incident_id"], inc_id)
            self.assertEqual(report["metrics_snapshot"], fetched_metrics)
            self.assertIn(fetched_logs.decode('utf-8'), report["recovery_logs_summary"])
            self.assertIn("Root cause identified.", report["root_cause"])


if __name__ == '__main__':
    unittest.main()