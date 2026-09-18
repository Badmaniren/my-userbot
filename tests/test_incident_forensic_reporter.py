import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
from skills.incident_forensic_reporter import start_new

class TestIncidentForensicReporter(unittest.TestCase):

    def _generate_random_string(self, length=10):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))

    def test_start_new_success_execution(self):
        incident_id = uuid.uuid4().hex
        telemetry_source = f"https://{self._generate_random_string()}.io/telemetry/{uuid.uuid4().hex}"
        raw_log_data = f"CRITICAL_EVENT_{uuid.uuid4().hex}: {self._generate_random_string(30)}"
        
        mock_response_data = {
            "incident_id": incident_id,
            "status": "compiled",
            "telemetry_source": telemetry_source,
            "forensic_hash": uuid.uuid4().hex
        }

        with patch('skills.incident_forensic_reporter.incident_aggregator') as mock_aggregator, \
             patch('skills.incident_forensic_reporter.telemetry_processor') as mock_telemetry, \
             patch('requests.post') as mock_requests_post:

            mock_aggregator.return_value = {"logs": [raw_log_data]}
            mock_telemetry.return_value = io.BytesIO(raw_log_data.encode('utf-8'))
            
            mock_resp_instance = MagicMock()
            mock_resp_instance.status_code = 200
            mock_resp_instance.json.return_value = mock_response_data
            mock_requests_post.return_value = mock_resp_instance

            result = start_new(incident_id, telemetry_source)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("incident_id"), incident_id)
            self.assertEqual(result.get("status"), "compiled")
            self.assertIn("forensic_hash", result)
            mock_aggregator.assert_called_once()
            mock_telemetry.assert_called_once()

    def test_start_new_empty_telemetry(self):
        incident_id = uuid.uuid4().hex
        telemetry_source = f"file:///var/log/{self._generate_random_string()}.log"

        with patch('skills.incident_forensic_reporter.incident_aggregator') as mock_aggregator, \
             patch('skills.incident_forensic_reporter.telemetry_streamer') as mock_streamer:

            mock_aggregator.return_value = {}
            mock_streamer.side_effect = FileNotFoundError(f"Path not found: {telemetry_source}")

            with self.assertRaises(FileNotFoundError):
                start_new(incident_id, telemetry_source)

            mock_aggregator.assert_called_once()
            mock_streamer.assert_called_once()

    def test_start_new_with_anomaly_evaluation(self):
        incident_id = uuid.uuid4().hex
        telemetry_source = f"tcp://{self._generate_random_string()}.internal:9999"
        expected_score = round(random.uniform(1.1, 9.9), 2)

        with patch('skills.incident_forensic_reporter.telemetry_anomaly_evaluator_core') as mock_evaluator, \
             patch('skills.incident_forensic_reporter.incident_severity_evaluator') as mock_severity:

            mock_evaluator.return_value = {"anomaly_score": expected_score}
            mock_severity.return_value = "HIGH"

            result = start_new(incident_id, telemetry_source, evaluate_anomalies=True)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("anomaly_score"), expected_score)
            self.assertEqual(result.get("severity"), "HIGH")
            mock_evaluator.assert_called_once()
            mock_severity.assert_called_once()

    def test_start_new_network_failure_handling(self):
        incident_id = uuid.uuid4().hex
        telemetry_source = f"https://{self._generate_random_string()}.net/api/v1/dump"

        with patch('skills.incident_forensic_reporter.incident_aggregator') as mock_aggregator, \
             patch('requests.post') as mock_requests_post:

            mock_aggregator.return_value = {"status": "ok"}
            mock_requests_post.side_effect = Exception(f"Connection timeout on {uuid.uuid4().hex}")

            with self.assertRaises(Exception):
                start_new(incident_id, telemetry_source)

            mock_requests_post.assert_called_once()

    def test_start_new_payload_integrity(self):
        incident_id = uuid.uuid4().hex
        telemetry_source = f"s3://{self._generate_random_string()}-bucket/{uuid.uuid4().hex}.parquet"
        random_payload_key = self._generate_random_string(12)
        random_payload_val = self._generate_random_string(12)

        captured_args = {}

        def side_effect_mock(*args, **kwargs):
            captured_args.update(kwargs.get('json', {}))
            resp = MagicMock()
            resp.status_code = 201
            resp.json.return_value = {"status": "stored", "key": random_payload_key}
            return resp

        with patch('skills.incident_forensic_reporter.incident_aggregator', return_value={random_payload_key: random_payload_val}), \
             patch('requests.post', side_effect=side_effect_mock) as mock_post:

            res = start_new(incident_id, telemetry_source)

            self.assertEqual(res.get("status"), "stored")
            self.assertEqual(res.get("key"), random_payload_key)
            self.assertIn(random_payload_key, captured_args.values() or captured_args.keys())
            mock_post.assert_called_once()

if __name__ == '__main__':
    unittest.main()