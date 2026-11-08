import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys

from skills.repo_health_pulse_engine import RepoHealthPulseEngine, PulseMetric, PulseException

class TestRepoHealthPulseEngine(unittest.TestCase):

    def setUp(self):
        self.engine = RepoHealthPulseEngine()
        self.random_repo_id = uuid.uuid4().hex
        self.random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_value = random.uniform(0.0, 100.0)

    def test_collect_pulse_metric_success(self):
        with patch('skills.repo_health_pulse_engine.RepoHealthPulseEngine._fetch_raw_metric') as mock_fetch:
            mock_fetch.return_value = self.random_value
            
            result = self.engine.collect_metric(self.random_repo_id, self.random_metric_name)
            
            self.assertIsInstance(result, PulseMetric)
            self.assertEqual(result.repo_id, self.random_repo_id)
            self.assertEqual(result.name, self.random_metric_name)
            self.assertEqual(result.value, self.random_value)
            mock_fetch.assert_called_once_with(self.random_repo_id, self.random_metric_name)

    def test_collect_pulse_metric_safe_exception_handling(self):
        with patch('skills.repo_health_pulse_engine.RepoHealthPulseEngine._fetch_raw_metric') as mock_fetch:
            random_error_msg = uuid.uuid4().hex
            mock_fetch.side_effect = Exception(random_error_msg)
            
            result = self.engine.collect_metric(self.random_repo_id, self.random_metric_name)
            
            self.assertIsInstance(result, PulseMetric)
            self.assertEqual(result.repo_id, self.random_repo_id)
            self.assertEqual(result.name, self.random_metric_name)
            self.assertFalse(result.is_healthy)
            self.assertIn(random_error_msg, result.error_message)

    def test_pulse_stream_monitoring(self):
        random_iterations = random.randint(1, 5)
        raw_stream_data = io.BytesIO(f"repo:{self.random_repo_id},val:{self.random_value}\n".encode('utf-8'))
        
        with patch('skills.repo_health_pulse_engine.open', return_value=raw_stream_data):
            metrics = self.engine.monitor_stream(uuid.uuid4().hex, limit=random_iterations)
            
            self.assertIsInstance(metrics, list)
            self.assertTrue(len(metrics) <= random_iterations)

    def test_pulse_engine_diagnostic_export(self):
        random_diagnostic_key = uuid.uuid4().hex
        random_diagnostic_val = random.randint(1000, 9999)
        
        with patch('skills.repo_health_pulse_engine.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {random_diagnostic_key: random_diagnostic_val}
            mock_post.return_value = mock_response
            
            url = f"https://{uuid.uuid4().hex}.com/pulse"
            payload = {self.random_metric_name: self.random_value}
            
            response = self.engine.export_pulse(url, payload)
            
            self.assertEqual(response[random_diagnostic_key], random_diagnostic_val)
            mock_post.assert_called_once()

    def test_pulse_engine_diagnostic_export_failure(self):
        with patch('skills.repo_health_pulse_engine.requests.post') as mock_post:
            mock_post.side_effect = TimeoutError(uuid.uuid4().hex)
            
            url = f"https://{uuid.uuid4().hex}.com/pulse"
            payload = {self.random_metric_name: self.random_value}
            
            with self.assertRaises(PulseException):
                self.engine.export_pulse(url, payload)

if __name__ == '__main__':
    unittest.main()