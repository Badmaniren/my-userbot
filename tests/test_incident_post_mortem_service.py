import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json
from skills.incident_post_mortem_service import IncidentPostMortemService

class TestIncidentPostMortemService(unittest.TestCase):
    def setUp(self):
        self.service = IncidentPostMortemService()

    def test_generate_post_mortem_report_success(self):
        rand_incident_id = uuid.uuid4().hex
        rand_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        rand_metric_value = random.uniform(10.0, 500.0)
        rand_log_line = f"ERROR: {uuid.uuid4().hex} failed to process request"
        
        metrics_data = {
            rand_metric_name: rand_metric_value,
            "error_rate": random.randint(5, 50)
        }
        logs_stream = io.BytesIO(rand_log_line.encode('utf-8'))

        with patch('skills.incident_post_mortem_service.IncidentPostMortemService._fetch_incident_metrics', return_value=metrics_data) as mock_metrics, \
             patch('skills.incident_post_mortem_service.IncidentPostMortemService._fetch_recovery_logs', return_value=logs_stream) as mock_logs:
            
            report = self.service.generate_report(rand_incident_id)

            mock_metrics.assert_called_once_with(rand_incident_id)
            mock_logs.assert_called_once_with(rand_incident_id)

            self.assertIsInstance(report, dict)
            self.assertEqual(report.get("incident_id"), rand_incident_id)
            self.assertIn("timeline", report)
            self.assertIn("root_cause", report)
            self.assertIn(rand_metric_name, report.get("metrics_snapshot", {}))
            self.assertEqual(report["metrics_snapshot"][rand_metric_name], rand_metric_value)
            self.assertIn(rand_log_line, report.get("recovery_logs_summary", ""))

    def test_generate_post_mortem_report_empty_logs(self):
        rand_incident_id = uuid.uuid4().hex
        metrics_data = {"cpu_load": random.randint(80, 100)}
        empty_stream = io.BytesIO(b"")

        with patch('skills.incident_post_mortem_service.IncidentPostMortemService._fetch_incident_metrics', return_value=metrics_data), \
             patch('skills.incident_post_mortem_service.IncidentPostMortemService._fetch_recovery_logs', return_value=empty_stream):
            
            report = self.service.generate_report(rand_incident_id)

            self.assertIsInstance(report, dict)
            self.assertEqual(report.get("incident_id"), rand_incident_id)
            self.assertEqual(report.get("recovery_logs_summary"), "")

    def test_parse_recovery_logs_stream(self):
        rand_uuid1 = uuid.uuid4().hex
        rand_uuid2 = uuid.uuid4().hex
        raw_logs = f"[INFO] Start {rand_uuid1}\n[ERROR] Crash {rand_uuid2}\n[INFO] Recovered".encode('utf-8')
        log_stream = io.BytesIO(raw_logs)

        parsed_data = self.service._parse_recovery_logs(log_stream)

        self.assertIsInstance(parsed_data, list)
        self.assertGreaterEqual(len(parsed_data), 2)
        joined_logs = " ".join(parsed_data)
        self.assertIn(rand_uuid1, joined_logs)
        self.assertIn(rand_uuid2, joined_logs)

    def test_evaluate_root_cause_logic(self):
        rand_keyword = ''.join(random.choices(string.ascii_uppercase, k=6))
        metrics = {
            "timeout_count": random.randint(100, 1000),
            "memory_leak_detected": True
        }
        logs = [f"CRITICAL: {rand_keyword} subsystem failure", "INFO: restarting node"]

        root_cause = self.service._evaluate_root_cause(metrics, logs)

        self.assertIsInstance(root_cause, str)
        self.assertIn(rand_keyword, root_cause)
        self.assertIn("memory", root_cause.lower())

if __name__ == '__main__':
    unittest.main()