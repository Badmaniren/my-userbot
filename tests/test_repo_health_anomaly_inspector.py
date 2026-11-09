import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.metric_name_neg = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.metric_name_high = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.metric_name_normal = ''.join(random.choices(string.ascii_lowercase, k=8))

    def test_init_default_engine(self):
        inspector = RepoHealthAnomalyInspector()
        self.assertIsNotNone(inspector.pulse_engine)
        self.assertIsNotNone(inspector.logger)

    def test_inspect_with_explicit_payload_no_anomalies(self):
        val_normal = random.uniform(0.0, 50.0)
        payload = {
            "metrics": {
                self.metric_name_normal: val_normal
            }
        }
        threshold = random.uniform(51.0, 100.0)
        
        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(self.repo_id, pulse_payload=payload, threshold=threshold)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 0)
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_detects_negative_anomaly(self):
        neg_val = -float(random.randint(1, 100))
        payload = {
            "metrics": {
                self.metric_name_neg: neg_val
            }
        }

        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(self.repo_id, pulse_payload=payload)

        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_neg)
        self.assertEqual(result["anomalies"][0]["value"], neg_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")
        self.assertEqual(result["deviation_score"], abs(neg_val))

    def test_inspect_detects_high_anomaly(self):
        threshold = float(random.randint(10, 50))
        high_val = threshold + float(random.randint(1, 50))
        payload = {
            "metrics": {
                self.metric_name_high: high_val
            }
        }

        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(self.repo_id, pulse_payload=payload, threshold=threshold)

        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_high)
        self.assertEqual(result["anomalies"][0]["value"], high_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "high")
        self.assertEqual(result["deviation_score"], high_val - threshold)

    def test_inspect_fetches_pulse_via_get_pulse(self):
        mock_engine = MagicMock()
        neg_val = -float(random.randint(1, 50))
        mock_engine.get_pulse.return_value = {
            "metrics": {
                self.metric_name_neg: neg_val
            }
        }
        del mock_engine.pulse

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.repo_id)

        mock_engine.get_pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["anomalies"][0]["value"], neg_val)

    def test_inspect_fetches_pulse_via_pulse_method(self):
        mock_engine = MagicMock()
        del mock_engine.get_pulse
        high_val = float(random.randint(100, 200))
        threshold = 50.0
        mock_engine.pulse.return_value = {
            "metrics": {
                self.metric_name_high: high_val
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.repo_id, threshold=threshold)

        mock_engine.pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["deviation_score"], high_val - threshold)

    def test_inspect_handles_none_payload_gracefully(self):
        mock_engine = MagicMock()
        del mock_engine.get_pulse
        del mock_engine.pulse

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.repo_id, pulse_payload=None)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)


if __name__ == '__main__':
    unittest.main()