import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector

class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.random_repo_id = str(uuid.uuid4())
        self.random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.negative_value = -float(random.randint(1, 100))
        self.high_value = float(random.randint(101, 1000))
        self.normal_value = float(random.randint(0, 50))
        self.threshold = float(random.randint(50, 100))

    def test_init_with_default_dependencies(self):
        with patch('skills.repo_health_anomaly_inspector.RepoHealthPulseEngine') as mock_pulse_engine, \
             patch('skills.repo_health_anomaly_inspector.RepoLogger') as mock_logger:
            
            inspector = RepoHealthAnomalyInspector()
            self.assertIsNotNone(inspector.pulse_engine)
            self.assertIsNotNone(inspector.logger)
            mock_pulse_engine.assert_called_once()

    def test_init_with_custom_dependencies_and_logger_type_error(self):
        custom_pulse = MagicMock()
        with patch('skills.repo_health_anomaly_inspector.RepoLogger', side_effect=TypeError("Invalid init")) as mock_logger:
            inspector = RepoHealthAnomalyInspector(pulse_engine=custom_pulse)
            self.assertEqual(inspector.pulse_engine, custom_pulse)
            self.assertEqual(mock_logger.call_count, 2)

    def test_inspect_with_explicit_payload_negative_anomaly(self):
        payload = {
            "metrics": {
                self.random_metric_name: self.negative_value
            }
        }
        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(self.random_repo_id, pulse_payload=payload)

        self.assertEqual(result["repo_id"], self.random_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.random_metric_name)
        self.assertEqual(result["anomalies"][0]["value"], self.negative_value)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")
        self.assertEqual(result["deviation_score"], abs(self.negative_value))

    def test_inspect_with_explicit_payload_high_anomaly(self):
        payload = {
            "metrics": {
                self.random_metric_name: self.high_value
            }
        }
        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(self.random_repo_id, pulse_payload=payload, threshold=self.threshold)

        self.assertEqual(result["repo_id"], self.random_repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["deviation"], "high")
        expected_score = self.high_value - self.threshold
        self.assertAlmostEqual(result["deviation_score"], expected_score)

    def test_inspect_with_normal_metrics_no_anomalies(self):
        payload = {
            "metrics": {
                self.random_metric_name: self.normal_value
            }
        }
        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(self.random_repo_id, pulse_payload=payload, threshold=self.threshold)

        self.assertEqual(result["repo_id"], self.random_repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 0)
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_fetches_pulse_via_get_pulse(self):
        mock_engine = MagicMock()
        payload = {
            "metrics": {
                self.random_metric_name: self.negative_value
            }
        }
        mock_engine.get_pulse.return_value = payload
        del mock_engine.pulse

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.random_repo_id)

        mock_engine.get_pulse.assert_called_once_with(self.random_repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["repo_id"], self.random_repo_id)

    def test_inspect_fetches_pulse_via_pulse_method(self):
        mock_engine = MagicMock()
        payload = {
            "metrics": {
                self.random_metric_name: self.normal_value
            }
        }
        del mock_engine.get_pulse
        mock_engine.pulse.return_value = payload

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.random_repo_id)

        mock_engine.pulse.assert_called_once_with(self.random_repo_id)
        self.assertFalse(result["is_anomaly"])

    def test_inspect_pulse_payload_none_fallback(self):
        mock_engine = MagicMock()
        mock_engine.get_pulse.return_value = None

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.random_repo_id)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_non_numeric_metrics_ignored(self):
        non_numeric_metric = f"str_metric_{uuid.uuid4().hex[:6]}"
        random_string_val = uuid.uuid4().hex
        payload = {
            "metrics": {
                non_numeric_metric: random_string_val
            }
        }
        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(self.random_repo_id, pulse_payload=payload)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 0)

    def test_io_stream_mock_integration(self):
        garbage_bytes = f"garbage_data_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(garbage_bytes)
        
        mock_engine = MagicMock()
        mock_engine.get_pulse.return_value = {
            "metrics": {
                "stream_read_test": stream.read().decode('utf-8')
            }
        }
        
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.random_repo_id)
        
        self.assertEqual(result["repo_id"], self.random_repo_id)
        self.assertFalse(result["is_anomaly"])

if __name__ == '__main__':
    unittest.main()