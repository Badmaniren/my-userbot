import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.system_telemetry_collector import SystemTelemetryCollector

class TestSystemTelemetryCollector(unittest.TestCase):

    def setUp(self):
        self.collector = SystemTelemetryCollector()
        self.random_module = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_incident = uuid.uuid4().hex
        self.random_error = ''.join(random.choices(string.ascii_letters, k=25))
        self.random_url = f"https://telemetry.{uuid.uuid4().hex[:8]}.internal/collect"

    def test_collect_and_send_telemetry_success(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = random.randint(1, 1000)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "acknowledged", "id": uuid.uuid4().hex}

        with patch('requests.post', return_value=mock_response) as mock_post:
            result = self.collector.collect_and_send(
                endpoint=self.random_url,
                module_name=self.random_module,
                metric_type=metric_name,
                value=metric_value
            )
            
            self.assertTrue(result)
            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            self.assertEqual(called_args[0], self.random_url)
            
            payload = called_kwargs.get('json', {})
            self.assertEqual(payload.get('module'), self.random_module)
            self.assertEqual(payload.get('metric'), metric_name)
            self.assertEqual(payload.get('value'), metric_value)

    def test_collect_and_send_telemetry_failure(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = random.uniform(0.1, 99.9)

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = f"Internal Server Error {uuid.uuid4().hex[:4]}"

        with patch('requests.post', return_value=mock_response) as mock_post:
            result = self.collector.collect_and_send(
                endpoint=self.random_url,
                module_name=self.random_module,
                metric_type=metric_name,
                value=metric_value
            )
            
            self.assertFalse(result)
            mock_post.assert_called_once()

    def test_aggregate_incident_metrics(self):
        incident_count = random.randint(3, 10)
        incidents_data = []
        for _ in range(incident_count):
            incidents_data.append({
                "incident_id": uuid.uuid4().hex,
                "module": self.random_module,
                "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
                "resolved": random.choice([True, False])
            })

        stream_data = json.dumps(incidents_data).encode('utf-8')
        mock_stream = io.BytesIO(stream_data)

        summary = self.collector.aggregate_metrics_from_stream(mock_stream)

        self.assertIsInstance(summary, dict)
        self.assertEqual(summary.get("total_incidents"), incident_count)
        self.assertIn("resolved_count", summary)
        self.assertIn("critical_count", summary)

    def test_export_telemetry_report_to_file(self):
        file_path = f"/tmp/telemetry_{uuid.uuid4().hex}.json"
        report_payload = {
            "session_id": uuid.uuid4().hex,
            "error_rate": random.random(),
            "target_module": self.random_module
        }

        mock_file = MagicMock()
        with patch('builtins.open', return_value=mock_file) as mock_open:
            success = self.collector.export_report(report_payload, file_path)
            
            self.assertTrue(success)
            mock_open.assert_called_once_with(file_path, 'w', encoding='utf-8')
            mock_file.__enter__().write.assert_called_once()
            
            written_data = mock_file.__enter__().write.call_args[0][0]
            parsed_data = json.loads(written_data)
            self.assertEqual(parsed_data.get("session_id"), report_payload["session_id"])

    def test_process_stream_data_invalid_json(self):
        garbage_bytes = b"".join([uuid.uuid4().bytes for _ in range(3)])
        mock_stream = io.BytesIO(garbage_bytes)

        result = self.collector.aggregate_metrics_from_stream(mock_stream)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("total_incidents"), 0)
        self.assertTrue(result.get("parse_error"))