import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.metric_name_neg = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.metric_name_high = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.metric_name_normal = ''.join(random.choices(string.ascii_lowercase, k=10))
        
        self.negative_value = -float(random.randint(1, 100))
        self.high_value = float(random.randint(50, 200))
        self.threshold = float(random.randint(10, 40))
        self.normal_value = float(random.randint(0, int(self.threshold)))

    def test_init_defaults(self):
        inspector = RepoHealthAnomalyInspector()
        self.assertIsNotNone(inspector.pulse_engine)
        self.assertIsNotNone(inspector.logger)

    def test_inspect_with_explicit_payload_negative_anomaly(self):
        pulse_payload = {
            "metrics": {
                self.metric_name_neg: self.negative_value,
                self.metric_name_normal: self.normal_value
            }
        }
        mock_pulse_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        
        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=pulse_payload)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_neg)
        self.assertEqual(result["anomalies"][0]["value"], self.negative_value)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")
        self.assertEqual(result["deviation_score"], abs(self.negative_value))
        mock_pulse_engine.get_pulse.assert_not_called()

    def test_inspect_with_explicit_payload_high_anomaly(self):
        pulse_payload = {
            "metrics": {
                self.metric_name_high: self.high_value,
                self.metric_name_normal: self.normal_value
            }
        }
        mock_pulse_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        
        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=pulse_payload, threshold=self.threshold)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_high)
        self.assertEqual(result["anomalies"][0]["value"], self.high_value)
        self.assertEqual(result["anomalies"][0]["deviation"], "high")
        self.assertAlmostEqual(result["deviation_score"], self.high_value - self.threshold)

    def test_inspect_fallback_to_get_pulse(self):
        pulse_payload = {
            "metrics": {
                self.metric_name_normal: self.normal_value
            }
        }
        mock_pulse_engine = MagicMock()
        mock_pulse_engine.get_pulse.return_value = pulse_payload
        
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(repo_id=self.repo_id)

        mock_pulse_engine.get_pulse.assert_called_once_with(self.repo_id)
        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_fallback_to_pulse_method(self):
        pulse_payload = {
            "metrics": {
                self.metric_name_neg: self.negative_value
            }
        }
        mock_pulse_engine = MagicMock(spec=[])
        mock_pulse_engine.pulse = MagicMock(return_value=pulse_payload)
        
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(repo_id=self.repo_id)

        mock_pulse_engine.pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)

    def test_inspect_pulse_engine_returns_none(self):
        mock_pulse_engine = MagicMock()
        mock_pulse_engine.get_pulse.return_value = None
        
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(repo_id=self.repo_id)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_pulse_engine_no_methods(self):
        mock_pulse_engine = MagicMock(spec=[])
        
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(repo_id=self.repo_id)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)


if __name__ == "__main__":
    unittest.main()