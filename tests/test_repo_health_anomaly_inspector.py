import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.metric_name_neg = uuid.uuid4().hex
        self.metric_name_high = uuid.uuid4().hex
        self.metric_name_normal = uuid.uuid4().hex

    def test_init_default_engines(self):
        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine") as mock_engine_cls, \
             patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            
            mock_engine_instance = MagicMock()
            mock_engine_cls.return_value = mock_engine_instance

            inspector = RepoHealthAnomalyInspector()
            self.assertEqual(inspector.pulse_engine, mock_engine_instance)
            mock_logger_cls.assert_called()

    def test_init_with_custom_pulse_engine(self):
        custom_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)
        self.assertEqual(inspector.pulse_engine, custom_engine)

    def test_inspect_fetches_pulse_via_get_pulse(self):
        mock_engine = MagicMock()
        negative_val = -random.randint(1, 100)
        mock_payload = {
            "metrics": {
                self.metric_name_neg: negative_val
            }
        }
        mock_engine.get_pulse.return_value = mock_payload
        if hasattr(mock_engine, "pulse"):
            delattr(mock_engine, "pulse")

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.repo_id)

        mock_engine.get_pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_neg)
        self.assertEqual(result["anomalies"][0]["value"], negative_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")

    def test_inspect_fetches_pulse_via_pulse_method(self):
        mock_engine = MagicMock()
        if hasattr(mock_engine, "get_pulse"):
            delattr(mock_engine, "get_pulse")
        
        high_val = random.randint(100, 1000)
        threshold = high_val - random.randint(1, 10)
        mock_payload = {
            "metrics": {
                self.metric_name_high: high_val
            }
        }
        mock_engine.pulse.return_value = mock_payload

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.repo_id, threshold=threshold)

        mock_engine.pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_high)
        self.assertEqual(result["anomalies"][0]["value"], high_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "high")

    def test_inspect_pulse_payload_none_fallback(self):
        mock_engine = MagicMock()
        mock_engine.get_pulse.return_value = None

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.repo_id, pulse_payload=None)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)
        self.assertEqual(result["status"], "inspected")

    def test_inspect_mixed_metrics_and_threshold(self):
        negative_val = -random.randint(1, 50)
        high_val = random.randint(500, 1000)
        normal_val = random.randint(10, 50)
        threshold = random.randint(100, 200)

        pulse_payload = {
            "metrics": {
                self.metric_name_neg: negative_val,
                self.metric_name_high: high_val,
                self.metric_name_normal: normal_val
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=MagicMock())
        result = inspector.inspect(self.repo_id, pulse_payload=pulse_payload, threshold=threshold)

        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 2)
        
        expected_deviation_score = abs(negative_val) + (high_val - threshold)
        self.assertEqual(result["deviation_score"], expected_deviation_score)

        anomaly_metrics = {item["metric"] for item in result["anomalies"]}
        self.assertIn(self.metric_name_neg, anomaly_metrics)
        self.assertIn(self.metric_name_high, anomaly_metrics)
        self.assertNotIn(self.metric_name_normal, anomaly_metrics)

    def test_inspect_no_anomalies(self):
        normal_val = random.randint(0, 50)
        threshold = random.randint(100, 200)

        pulse_payload = {
            "metrics": {
                self.metric_name_normal: normal_val
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=MagicMock())
        result = inspector.inspect(self.repo_id, pulse_payload=pulse_payload, threshold=threshold)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 0)
        self.assertEqual(result["deviation_score"], 0.0)


if __name__ == "__main__":
    unittest.main()