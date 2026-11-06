import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.repo_health_pulse import (
    RepoHealthPulseCollector,
    RepoHealthTrendAnalyzer,
    RepoHealthMetric,
    RepoHealthDegradationError
)

class TestRepoHealthPulse(unittest.TestCase):

    def setUp(self):
        self.metric_name = ''.join(random.choices(string.ascii_lowercase, k=12))
        self.repo_path = f"/repo/{uuid.uuid4().hex[:8]}"
        self.collector = RepoHealthPulseCollector(repo_path=self.repo_path)
        self.analyzer = RepoHealthTrendAnalyzer()

    def test_collect_metric_success(self):
        dynamic_value = round(random.uniform(0.0, 100.0), 2)
        dynamic_raw_data = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}
        
        mock_output = json.dumps({
            "metric": self.metric_name,
            "value": dynamic_value,
            "details": dynamic_raw_data
        }).encode('utf-8')

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr=b""
            )
            
            result = self.collector.collect_metric(self.metric_name)
            
            self.assertIsInstance(result, RepoHealthMetric)
            self.assertEqual(result.name, self.metric_name)
            self.assertEqual(result.value, dynamic_value)
            self.assertEqual(result.details, dynamic_raw_data)
            mock_run.assert_called_once()

    def test_collect_metric_execution_failure_raises_error(self):
        err_msg = uuid.uuid4().hex.encode('utf-8')
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=random.randint(1, 255),
                stdout=b"",
                stderr=err_msg
            )
            
            with self.assertRaises(RepoHealthDegradationError) as ctx:
                self.collector.collect_metric(self.metric_name)
            
            self.assertIn(err_msg.decode('utf-8'), str(ctx.exception))

    def test_trend_analyzer_detects_degradation(self):
        historical_values = [random.uniform(10.0, 20.0) for _ in range(5)]
        degraded_value = historical_values[-1] + random.uniform(50.0, 100.0)
        
        metrics_sequence = [
            RepoHealthMetric(name=self.metric_name, value=val, details={})
            for val in historical_values
        ]
        metrics_sequence.append(RepoHealthMetric(name=self.metric_name, value=degraded_value, details={}))

        is_degrading = self.analyzer.analyze_trend(metrics_sequence)
        self.assertTrue(is_degrading)

    def test_trend_analyzer_stable_code(self):
        stable_values = [random.uniform(40.0, 50.0) for _ in range(6)]
        metrics_sequence = [
            RepoHealthMetric(name=self.metric_name, value=val, details={})
            for val in stable_values
        ]

        is_degrading = self.analyzer.analyze_trend(metrics_sequence)
        self.assertFalse(is_degrading)

    def test_pulse_stream_parsing_with_io(self):
        random_key = uuid.uuid4().hex
        random_val = random.randint(100, 999)
        mock_payload = f"{random_key}:{random_val}\n".encode('utf-8')
        
        mock_stream = io.BytesIO(mock_payload)

        with patch('skills.repo_health_pulse.open', return_value=mock_stream, create=True):
            parsed_data = self.collector.parse_health_stream(uuid.uuid4().hex)
            self.assertEqual(parsed_data.get(random_key), random_val)

    def test_guardian_circuit_breaker_on_severe_degradation(self):
        limit_threshold = random.uniform(1.0, 10.0)
        outrageous_value = limit_threshold + random.uniform(100.0, 500.0)
        
        metric = RepoHealthMetric(name=self.metric_name, value=outrageous_value, details={})

        with patch('skills.repo_health_pulse.RepoHealthPulseCollector.collect_metric', return_value=metric):
            with self.assertRaises(RepoHealthDegradationError):
                self.collector.enforce_health_guard(threshold=limit_threshold)

if __name__ == '__main__':
    unittest.main()