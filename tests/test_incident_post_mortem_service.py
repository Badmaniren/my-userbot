import io
import random
import uuid
import unittest
from unittest.mock import MagicMock, patch

from skills.incident_post_mortem_service import IncidentPostMortemService


class TestIncidentPostMortemService(unittest.TestCase):
    def setUp(self):
        self.service = IncidentPostMortemService()

    def test_fetch_incident_metrics_dict_return(self):
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(100, 999)
        rand_id = uuid.uuid4().hex

        with patch.object(self.service.incident_aggregator, 'aggregate', return_value={rand_key: rand_val}) as mock_agg:
            metrics = self.service._fetch_incident_metrics(rand_id)
            mock_agg.assert_called_once_with(rand_id)
            self.assertIsInstance(metrics, dict)
            self.assertEqual(metrics.get(rand_key), rand_val)

    def test_fetch_incident_metrics_non_dict_return(self):
        rand_id = uuid.uuid4().hex
        rand_bad_return = random.choice([uuid.uuid4().hex, random.randint(1, 100), None, [1, 2, 3]])

        with patch.object(self.service.incident_aggregator, 'aggregate', return_value=rand_bad_return) as mock_agg:
            metrics = self.service._fetch_incident_metrics(rand_id)
            mock_agg.assert_called_once_with(rand_id)
            self.assertEqual(metrics, {})

    def test_fetch_recovery_logs_bytes(self):
        rand_id = uuid.uuid4().hex
        rand_msg = uuid.uuid4().hex.encode('utf-8')

        with patch.object(self.service.error_recovery_hub, 'get_logs', return_value=rand_msg) as mock_logs:
            stream = self.service._fetch_recovery_logs(rand_id)
            mock_logs.assert_called_once_with(rand_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), rand_msg)

    def test_fetch_recovery_logs_string(self):
        rand_id = uuid.uuid4().hex
        rand_msg = uuid.uuid4().hex

        with patch.object(self.service.error_recovery_hub, 'get_logs', return_value=rand_msg) as mock_logs:
            stream = self.service._fetch_recovery_logs(rand_id)
            mock_logs.assert_called_once_with(rand_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read().decode('utf-8'), rand_msg)

    def test_fetch_recovery_logs_unsupported_type(self):
        rand_id = uuid.uuid4().hex
        rand_bad_type = random.choice([random.randint(1000, 9999), {"error": uuid.uuid4().hex}, None])

        with patch.object(self.service.error_recovery_hub, 'get_logs', return_value=rand_bad_type) as mock_logs:
            stream = self.service._fetch_recovery_logs(rand_id)
            mock_logs.assert_called_once_with(rand_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), b"")

    def test_parse_recovery_logs_valid(self):
        line1 = uuid.uuid4().hex
        line2 = uuid.uuid4().hex
        raw_data = f"\n  {line1} \n\n {line2}  \n".encode('utf-8')
        stream = io.BytesIO(raw_data)

        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [line1, line2])

    def test_parse_recovery_logs_empty(self):
        stream = io.BytesIO(b"")
        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [])

    def test_evaluate_root_cause_complex(self):
        timeout_val = random.randint(10, 100)
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

    def test_evaluate_root_cause_empty(self):
        cause = self.service._evaluate_root_cause({}, [])
        self.assertIn("Root cause identified.", cause)

    def test_generate_report_with_dict_incident(self):
        rand_incident_id = uuid.uuid4().hex
        rand_error_code = f"ERR-{random.randint(1000, 9999)}"
        rand_metric_val = random.randint(50, 500)
        rand_log_msg = uuid.uuid4().hex

        incident_dict = {
            "incident_id": rand_incident_id,
            "error_code": rand_error_code,
            "metrics": {
                "memory_leak_mb": rand_metric_val
            }
        }
        recovery_data = {
            "logs": rand_log_msg.encode('utf-8')
        }

        with patch.object(self.service.report_exporter, 'export') as mock_export:
            report = self.service.generate_report(incident_dict, recovery_data)
            mock_export.assert_called_once()
            self.assertEqual(report["incident_id"], rand_incident_id)
            self.assertIn("report_id", report)
            self.assertIn(rand_error_code, report["root_cause_analysis"])
            self.assertIn(rand_log_msg, report["recovery_logs_summary"])
            self.assertEqual(report["metrics_snapshot"]["memory_leak_mb"], rand_metric_val)

    def test_generate_report_with_string_incident(self):
        rand_incident_id = uuid.uuid4().hex
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(1, 99)
        rand_log_content = uuid.uuid4().hex

        with patch.object(self.service, '_fetch_incident_metrics', return_value={rand_metric_key: rand_metric_val}) as mock_metrics, \
             patch.object(self.service, '_fetch_recovery_logs', return_value=io.BytesIO(rand_log_content.encode('utf-8'))) as mock_logs, \
             patch.object(self.service.report_exporter, 'export') as mock_export:
            
            report = self.service.generate_report(rand_incident_id)
            
            mock_metrics.assert_called_once_with(rand_incident_id)
            mock_logs.assert_called_once_with(rand_incident_id)
            mock_export.assert_called_once()

            self.assertEqual(report["incident_id"], rand_incident_id)
            self.assertEqual(report["metrics_snapshot"][rand_metric_key], rand_metric_val)
            self.assertIn(rand_log_content, report["recovery_logs_summary"])
            self.assertIn("Root cause identified.", report["root_cause"])


if __name__ == '__main__':
    unittest.main()