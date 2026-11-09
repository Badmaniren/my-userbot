import unittest
from unittest.mock import MagicMock, patch
import random
import uuid
import string

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.metric_name_neg = "".join(random.choices(string.ascii_lowercase, k=8))
        self.metric_name_high = "".join(random.choices(string.ascii_lowercase, k=8))
        self.metric_name_norm = "".join(random.choices(string.ascii_lowercase, k=8))
        
        self.negative_value = -float(random.randint(1, 100))
        self.high_value = float(random.randint(101, 1000))
        self.normal_value = float(random.randint(0, 50))
        self.threshold = float(random.randint(50, 100))

    def test_init_default_engine(self):
        inspector = RepoHealthAnomalyInspector()
        self.assertIsNotNone(inspector.pulse_engine)
        self.assertIsNotNone(inspector.logger)

    def test_inspect_with_explicit_payload(self):
        pulse_payload = {
            "metrics": {
                self.metric_name_neg: self.negative_value,
                self.metric_name_high: self.high_value,
                self.metric_name_norm: self.normal_value
            }
        }

        mock_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)

        result = inspector.inspect(self.repo_id, pulse_payload=pulse_payload, threshold=self.threshold)

        mock_engine.get_pulse.assert_not_called()
        mock_engine.pulse.assert_not_called()

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 2)
        
        expected_deviation = abs(self.negative_value) + (self.high_value - self.threshold)
        self.assertAlmostEqual(result["deviation_score"], expected_deviation)

    def test_inspect_calls_get_pulse(self):
        pulse_payload = {
            "metrics": {
                self.metric_name_norm: self.normal_value
            }
        }

        mock_engine = MagicMock()
        mock_engine.get_pulse.return_value = pulse_payload
        del mock_engine.pulse

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.repo_id)

        mock_engine.get_pulse.assert_called_once_with(self.repo_id)
        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_calls_pulse_fallback(self):
        pulse_payload = {
            "metrics": {
                self.metric_name_neg: self.negative_value
            }
        }

        mock_engine = MagicMock()
        del mock_engine.get_pulse
        mock_engine.pulse.return_value = pulse_payload

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.repo_id)

        mock_engine.pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_neg)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")

    def test_inspect_engine_returns_none(self):
        mock_engine = MagicMock()
        mock_engine.get_pulse.return_value = None

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.repo_id)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_engine_no_methods(self):
        class DummyEngine:
            pass

        dummy = DummyEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=dummy)
        result = inspector.inspect(self.repo_id)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])


if __name__ == "__main__":
    unittest.main()