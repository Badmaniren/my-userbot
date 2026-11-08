import unittest
from unittest.mock import MagicMock, patch
import random
import uuid
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector

class TestRepoHealthAnomalyInspector(unittest.TestCase):
    def setUp(self):
        self.repo_id = str(uuid.uuid4().hex)
        self.metric_name_neg = str(uuid.uuid4().hex)
        self.metric_name_high = str(uuid.uuid4().hex)
        self.metric_name_normal = str(uuid.uuid4().hex)
        self.negative_value = -float(random.randint(1, 100))
        self.high_value = float(random.randint(100, 200))
        self.threshold = float(random.randint(50, 99))
        self.normal_value = float(random.randint(0, 49))

    def test_init_default(self):
        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine") as mock_engine_class, \
             patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_class:
            
            inspector = RepoHealthAnomalyInspector()
            mock_engine_class.assert_called_once()
            mock_logger_class.assert_called_once()
            self.assertIsNotNone(inspector.pulse_engine)
            self.assertIsNotNone(inspector.logger)

    def test_init_with_custom_pulse_engine(self):
        custom_engine = MagicMock()
        with patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_class:
            inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)
            self.assertEqual(inspector.pulse_engine, custom_engine)
            mock_logger_class.assert_called_once()

    def test_inspect_fetches_pulse_when_payload_is_none(self):
        mock_engine = MagicMock()
        expected_payload = {
            "metrics": {
                self.metric_name_normal: self.normal_value
            }
        }
        mock_engine.get_pulse.return_value = expected_payload

        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
            result = inspector.inspect(self.repo_id)

            mock_engine.get_pulse.assert_called_once_with(self.repo_id)
            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertEqual(result["status"], "inspected")
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["anomalies"], [])
            self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_detects_negative_anomaly(self):
        mock_engine = MagicMock()
        pulse_payload = {
            "metrics": {
                self.metric_name_neg: self.negative_value
            }
        }

        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
            result = inspector.inspect(self.repo_id, pulse_payload=pulse_payload)

            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 1)
            self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_neg)
            self.assertEqual(result["anomalies"][0]["value"], self.negative_value)
            self.assertEqual(result["anomalies"][0]["deviation"], "negative")
            self.assertEqual(result["deviation_score"], abs(self.negative_value))

    def test_inspect_detects_high_anomaly_with_threshold(self):
        mock_engine = MagicMock()
        pulse_payload = {
            "metrics": {
                self.metric_name_high: self.high_value
            }
        }

        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
            result = inspector.inspect(self.repo_id, pulse_payload=pulse_payload, threshold=self.threshold)

            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 1)
            self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_high)
            self.assertEqual(result["anomalies"][0]["value"], self.high_value)
            self.assertEqual(result["anomalies"][0]["deviation"], "high")
            self.assertEqual(result["deviation_score"], self.high_value - self.threshold)

    def test_inspect_ignores_high_value_when_threshold_is_none(self):
        mock_engine = MagicMock()
        pulse_payload = {
            "metrics": {
                self.metric_name_high: self.high_value
            }
        }

        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
            result = inspector.inspect(self.repo_id, pulse_payload=pulse_payload, threshold=None)

            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["anomalies"], [])
            self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_handles_mixed_metrics_and_non_numeric(self):
        mock_engine = MagicMock()
        non_numeric_key = str(uuid.uuid4().hex)
        non_numeric_val = str(uuid.uuid4().hex)
        
        pulse_payload = {
            "metrics": {
                self.metric_name_neg: self.negative_value,
                self.metric_name_high: self.high_value,
                self.metric_name_normal: self.normal_value,
                non_numeric_key: non_numeric_val
            }
        }

        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
            result = inspector.inspect(self.repo_id, pulse_payload=pulse_payload, threshold=self.threshold)

            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 2)
            
            expected_deviation_score = abs(self.negative_value) + (self.high_value - self.threshold)
            self.assertEqual(result["deviation_score"], expected_deviation_score)

if __name__ == "__main__":
    unittest.main()