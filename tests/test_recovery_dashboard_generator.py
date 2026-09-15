import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.recovery_dashboard_generator import RecoveryDashboardGenerator


class TestRecoveryDashboardGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = RecoveryDashboardGenerator()
        self.random_module = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_incident_id = uuid.uuid4().hex
        self.random_error_msg = f"Error_{uuid.uuid4().hex[:6]}"
        self.random_epic_id = uuid.uuid4().hex

    def test_generate_dashboard_html_structure(self):
        metrics = {
            "total_incidents": random.randint(10, 100),
            "resolved_count": random.randint(5, 50),
            "system_health_score": round(random.uniform(0.0, 100.0), 2)
        }
        incidents = [
            {
                "id": self.random_incident_id,
                "module": self.random_module,
                "error": self.random_error_msg
            }
        ]
        reports = [
            {
                "epic_id": self.random_epic_id,
                "status": "completed"
            }
        ]

        html_output = self.generator.generate_dashboard(metrics, incidents, reports, format="html")

        self.assertIsInstance(html_output, str)
        self.assertIn(self.random_incident_id, html_output)
        self.assertIn(self.random_module, html_output)
        self.assertIn(str(metrics["total_incidents"]), html_output)
        self.assertTrue(html_output.strip().startswith("<!DOCTYPE html>") or "<html" in html_output)

    def test_generate_dashboard_json_structure(self):
        metrics = {
            "uptime": random.randint(1000, 99999),
            "active_streams": random.randint(1, 5)
        }
        incidents = [
            {
                "incident_id": self.random_incident_id,
                "error_details": self.random_error_msg
            }
        ]
        reports = []

        json_output = self.generator.generate_dashboard(metrics, incidents, reports, format="json")

        self.assertIsInstance(json_output, str)
        parsed_data = json.loads(json_output)
        
        self.assertIn("metrics", parsed_data)
        self.assertIn("incidents", parsed_data)
        self.assertEqual(parsed_data["metrics"]["uptime"], metrics["uptime"])
        self.assertEqual(parsed_data["incidents"][0]["incident_id"], self.random_incident_id)

    def test_aggregate_system_health_metrics_calculates_correctly(self):
        raw_metrics = [
            {"success": True, "latency": random.randint(10, 100)},
            {"success": False, "latency": random.randint(100, 500)},
            {"success": True, "latency": random.randint(20, 200)}
        ]

        with patch('skills.recovery_dashboard_generator.RecoveryDashboardGenerator._fetch_internal_metrics', return_value=raw_metrics):
            aggregated = self.generator.aggregate_system_health()

            self.assertIsInstance(aggregated, dict)
            self.assertEqual(aggregated["total_requests"], 3)
            self.assertEqual(aggregated["failed_requests"], 1)
            self.assertIn("average_latency", aggregated)

    def test_export_dashboard_to_file_success(self):
        random_path = f"/tmp/dashboard_{uuid.uuid4().hex}.html"
        mock_payload = f"<html><body>Dashboard {uuid.uuid4().hex}</body></html>"

        with patch("builtins.open", new_callable=unittest.mock.mock_open) as mock_file:
            result = self.generator.export_dashboard(mock_payload, random_path)

            mock_file.assert_called_once_with(random_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(mock_payload)
            self.assertTrue(result)

    def test_export_dashboard_to_file_handles_exception(self):
        random_path = f"/tmp/faulty_{uuid.uuid4().hex}.json"
        mock_payload = json.dumps({"status": self.random_error_msg})

        with patch("builtins.open", side_effect=IOError("Disk full")):
            result = self.generator.export_dashboard(mock_payload, random_path)
            self.assertFalse(result)

    def test_process_stream_data_parsing(self):
        stream_content = f'{{"metric": "{self.random_module}", "value": {random.randint(1, 500)}}}'
        stream_bytes = io.BytesIO(stream_content.encode('utf-8'))

        parsed = self.generator.parse_stream_data(stream_bytes)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["metric"], self.random_module)

    def test_process_stream_data_invalid_bytes(self):
        corrupted_bytes = io.BytesIO(b'\xff\xfe\x00\x00invalid_stream_garbage')

        parsed = self.generator.parse_stream_data(corrupted_bytes)
        self.assertIsNone(parsed)