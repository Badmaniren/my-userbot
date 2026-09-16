import io
import random
import unittest
import uuid
from unittest.mock import patch, MagicMock

from skills.incident_post_mortem_service import IncidentPostMortemService


class TestIncidentPostMortemService(unittest.TestCase):
    def setUp(self):
        self.service = IncidentPostMortemService()

    def test_parse_recovery_logs_empty(self):
        empty_stream = io.BytesIO(b"")
        result = self.service._parse_recovery_logs(empty_stream)
        self.assertEqual(result, [])

    def test_parse_recovery_logs_with_data(self):
        rand_line_1 = uuid.uuid4().hex
        rand_line_2 = uuid.uuid4().hex
        raw_data = f"\n  {rand_line_1} \n\n {rand_line_2} \t \n".encode('utf-8')
        stream = io.BytesIO(raw_data)
        result = self.service._parse_recovery_logs(stream)
        self.assertEqual(result, [rand_line_1, rand_line_2])

    def test_evaluate_root_cause_memory_leak(self):
        rand_mb = random.randint(100, 9999)
        metrics = {"memory_leak_mb": rand_mb}
        logs = [uuid.uuid4().hex]
        cause = self.service._evaluate_root_cause(metrics, logs)
        self.assertIn("Memory leak detected", cause)
        self.assertIn(logs[0], cause)

    def test_evaluate_root_cause_timeout(self):
        rand_timeouts = random.randint(1, 50)
        metrics = {"timeout_count": rand_timeouts}
        logs = []
        cause = self.service._evaluate_root_cause(metrics, logs)
        self.assertIn(f"High timeout count: {rand_timeouts}", cause)

    def test_generate_report_dict_incident_full(self):
        rand_incident_id = uuid.uuid4().hex
        rand_error_code = f"ERR-{random.randint(1000, 9999)}"
        rand_log_line = uuid.uuid4().hex
        rand_metric_val = random.randint(10, 500)

        incident_dict = {
            "incident_id": rand_incident_id,
            "error_code": rand_error_code,
            "metrics": {
                "memory_leak_detected": True,
                "custom_metric": rand_metric_val
            }
        }
        recovery_data = {
            "logs": rand_log_line.encode('utf-8')
        }

        report = self.service.generate_report(incident=incident_dict, recovery_data=recovery_data)
        
        self.assertEqual(report["incident_id"], rand_incident_id)
        self.assertIn("report_id", report)
        self.assertIn("timeline", report)
        self.assertIn(rand_error_code, report["root_cause_analysis"])
        self.assertIn("Memory leak detected", report["root_cause_analysis"])
        self.assertEqual(report["metrics_snapshot"]["custom_metric"], rand_metric_val)
        self.assertEqual(report["recovery_logs_summary"], rand_log_line)

    def test_generate_report_dict_incident_minimal(self):
        report = self.service.generate_report(incident={})
        self.assertIsInstance(report, dict)
        self.assertIn("report_id", report)
        self.assertIn("incident_id", report)
        self.assertIn("root_cause_analysis", report)

    def test_generate_report_string_incident(self):
        rand_incident_id = uuid.uuid4().hex
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = uuid.uuid4().hex
        rand_log_content = uuid.uuid4().hex

        with patch.object(self.service, '_fetch_incident_metrics', return_value={rand_metric_key: rand_metric_val}) as mock_metrics, \
             patch.object(self.service, '_fetch_recovery_logs', return_value=io.BytesIO(rand_log_content.encode('utf-8'))) as mock_logs:

            report = self.service.generate_report(incident=rand_incident_id)

            mock_metrics.assert_called_once_with(rand_incident_id)
            mock_logs.assert_called_once_with(rand_incident_id)

            self.assertEqual(report["incident_id"], rand_incident_id)
            self.assertIn("root_cause", report)
            self.assertEqual(report["metrics_snapshot"][rand_metric_key], rand_metric_val)
            self.assertEqual(report["recovery_logs_summary"], rand_log_content)


if __name__ == '__main__':
    unittest.main()