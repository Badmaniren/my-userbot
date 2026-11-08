import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.mock_pulse_engine = MagicMock()
        self.inspector = RepoHealthAnomalyInspector(pulse_engine=self.mock_pulse_engine)

    def test_init_default_pulse_engine(self):
        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine") as mock_engine_cls:
            inspector = RepoHealthAnomalyInspector()
            self.assertEqual(inspector.pulse_engine, mock_engine_cls.return_value)

    def test_inspect_fetches_pulse_when_none(self):
        random_metric = uuid.uuid4().hex
        random_value = -random.randint(1, 100)
        
        self.mock_pulse_engine.get_pulse.return_value = {
            "metrics": {
                random_metric: random_value
            }
        }

        result = self.inspector.inspect(self.repo_id, pulse_payload=None)

        self.mock_pulse_engine.get_pulse.assert_called_once_with(self.repo_id)
        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], random_metric)
        self.assertEqual(result["anomalies"][0]["value"], random_value)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")

    def test_inspect_fallback_to_pulse_method(self):
        del self.mock_pulse_engine.get_pulse
        self.mock_pulse_engine.pulse = MagicMock(return_value={"metrics": {}})

        result = self.inspector.inspect(self.repo_id, pulse_payload=None)

        self.mock_pulse_engine.pulse.assert_called_once_with(self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])

    def test_inspect_empty_pulse_fallback(self):
        if hasattr(self.mock_pulse_engine, "get_pulse"):
            del self.mock_pulse_engine.get_pulse
        if hasattr(self.mock_pulse_engine, "pulse"):
            del self.mock_pulse_engine.pulse

        result = self.inspector.inspect(self.repo_id, pulse_payload=None)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_with_negative_and_high_threshold_anomalies(self):
        metric_neg = uuid.uuid4().hex
        val_neg = -random.uniform(1.0, 50.0)
        
        metric_high = uuid.uuid4().hex
        threshold = random.uniform(10.0, 50.0)
        val_high = threshold + random.uniform(1.0, 50.0)

        metric_normal = uuid.uuid4().hex
        val_normal = threshold / 2.0

        payload = {
            "metrics": {
                metric_neg: val_neg,
                metric_high: val_high,
                metric_normal: val_normal
            }
        }

        result = self.inspector.inspect(self.repo_id, pulse_payload=payload, threshold=threshold)

        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 2)
        
        anomalies_map = {a["metric"]: a for a in result["anomalies"]}
        
        self.assertIn(metric_neg, anomalies_map)
        self.assertEqual(anomalies_map[metric_neg]["deviation"], "negative")
        self.assertEqual(anomalies_map[metric_neg]["value"], val_neg)

        self.assertIn(metric_high, anomalies_map)
        self.assertEqual(anomalies_map[metric_high]["deviation"], "high")
        self.assertEqual(anomalies_map[metric_high]["value"], val_high)

        expected_deviation_score = abs(val_neg) + (val_high - threshold)
        self.assertAlmostEqual(result["deviation_score"], expected_deviation_score)

    def test_inspect_null_pulse_payload_argument(self):
        result = self.inspector.inspect(self.repo_id, pulse_payload=None)
        self.assertEqual(result["status"], "inspected")
        self.assertFalse(result["is_anomaly"])


if __name__ == "__main__":
    unittest.main()