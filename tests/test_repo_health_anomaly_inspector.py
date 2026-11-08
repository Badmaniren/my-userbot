import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.random_repo_id = str(uuid.uuid4())
        self.metric_name_neg = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.metric_name_high = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.metric_name_normal = ''.join(random.choices(string.ascii_lowercase, k=8))

    def test_init_default_engines(self):
        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine") as mock_engine_cls, \
             patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            
            inspector = RepoHealthAnomalyInspector()
            mock_engine_cls.assert_called_once()
            mock_logger_cls.assert_called()
            self.assertIsNotNone(inspector.pulse_engine)
            self.assertIsNotNone(inspector.logger)

    def test_init_custom_pulse_engine(self):
        custom_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)
        self.assertEqual(inspector.pulse_engine, custom_engine)

    def test_inspect_with_explicit_pulse_payload(self):
        neg_val = -random.randint(1, 100)
        high_val = random.randint(100, 200)
        threshold = 50

        payload = {
            "metrics": {
                self.metric_name_neg: neg_val,
                self.metric_name_high: high_val,
                self.metric_name_normal: 10
            }
        }

        custom_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)

        result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload=payload, threshold=threshold)

        custom_engine.get_pulse.assert_not_called()
        custom_engine.pulse.assert_not_called()

        self.assertEqual(result["repo_id"], self.random_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 2)
        
        expected_deviation = abs(neg_val) + (high_val - threshold)
        self.assertAlmostEqual(result["deviation_score"], expected_deviation)

    def test_inspect_fetches_pulse_via_get_pulse(self):
        neg_val = -random.randint(1, 50)
        payload = {
            "metrics": {
                self.metric_name_neg: neg_val
            }
        }

        mock_engine = MagicMock(spec=["get_pulse"])
        mock_engine.get_pulse.return_value = payload

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id=self.random_repo_id)

        mock_engine.get_pulse.assert_called_once_with(self.random_repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_neg)
        self.assertEqual(result["anomalies"][0]["value"], neg_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")

    def test_inspect_fetches_pulse_via_pulse_method(self):
        high_val = random.randint(150, 300)
        threshold = 100
        payload = {
            "metrics": {
                self.metric_name_high: high_val
            }
        }

        class FallbackEngine:
            def __init__(self, data):
                self.data = data
            def pulse(self, repo_id):
                return self.data

        engine = FallbackEngine(payload)
        inspector = RepoHealthAnomalyInspector(pulse_engine=engine)

        result = inspector.inspect(repo_id=self.random_repo_id, threshold=threshold)

        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_high)
        self.assertEqual(result["anomalies"][0]["value"], high_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "high")
        self.assertEqual(result["deviation_score"], high_val - threshold)

    def test_inspect_no_anomalies(self):
        normal_val = random.randint(0, 40)
        threshold = 50
        payload = {
            "metrics": {
                self.metric_name_normal: normal_val
            }
        }

        custom_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)

        result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload=payload, threshold=threshold)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_handles_none_payload_gracefully(self):
        mock_engine = MagicMock()
        mock_engine.get_pulse.return_value = None

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id=self.random_repo_id)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_ignores_non_numeric_metrics(self):
        string_val = ''.join(random.choices(string.ascii_letters, k=10))
        payload = {
            "metrics": {
                self.metric_name_normal: string_val,
                self.metric_name_high: None
            }
        }

        custom_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)

        result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload=payload, threshold=10)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)


if __name__ == '__main__':
    unittest.main()