import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.metric_name_neg = uuid.uuid4().hex
        self.metric_name_high = uuid.uuid4().hex
        self.metric_name_normal = uuid.uuid4().hex

    def test_init_default_engines(self):
        inspector = RepoHealthAnomalyInspector()
        self.assertIsNotNone(inspector.pulse_engine)
        self.assertIsNotNone(inspector.logger)

    def test_inspect_with_explicit_payload(self):
        rand_val_neg = -float(random.randint(1, 100))
        rand_val_high = float(random.randint(100, 200))
        threshold = 50.0

        payload = {
            "repo_id": self.repo_id,
            "metrics": {
                self.metric_name_neg: rand_val_neg,
                self.metric_name_high: rand_val_high,
                self.metric_name_normal: 10.0
            }
        }

        mock_pulse_engine = MagicMock()
        mock_logger = MagicMock()

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        inspector.logger = mock_logger

        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=payload, threshold=threshold)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 2)
        
        expected_deviation_score = abs(rand_val_neg) + (rand_val_high - threshold)
        self.assertAlmostEqual(result["deviation_score"], expected_deviation_score)
        mock_logger.info.assert_called_once()

    def test_inspect_fetches_from_pulse_engine_get_pulse(self):
        rand_val = -float(random.randint(1, 50))
        payload = {
            "repo_id": self.repo_id,
            "metrics": {
                self.metric_name_neg: rand_val
            }
        }

        mock_pulse_engine = MagicMock()
        mock_pulse_engine.get_pulse.return_value = payload

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=None)

        mock_pulse_engine.get_pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["repo_id"], self.repo_id)

    def test_inspect_fetches_from_pulse_engine_pulse(self):
        rand_val = float(random.randint(500, 1000))
        threshold = 100.0
        payload = {
            "metrics": {
                self.metric_name_high: rand_val
            }
        }

        mock_pulse_engine = MagicMock()
        del mock_pulse_engine.get_pulse
        mock_pulse_engine.pulse.return_value = payload

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(repo_id=self.repo_id, pulse_payload="invalid_payload", threshold=threshold)

        mock_pulse_engine.pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["repo_id"], self.repo_id)

    def test_inspect_no_anomalies(self):
        payload = {
            "repo_id": self.repo_id,
            "metrics": {
                self.metric_name_normal: float(random.randint(0, 40))
            }
        }

        mock_pulse_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=payload, threshold=50.0)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 0)
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_fallback_default_repo_id(self):
        payload = {
            "metrics": {
                self.metric_name_neg: -10.0
            }
        }
        mock_pulse_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        
        result = inspector.inspect(repo_id=None, pulse_payload=payload)
        self.assertEqual(result["repo_id"], "default-repo")

    def test_inspect_with_malformed_metrics(self):
        payload = {
            "repo_id": self.repo_id,
            "metrics": "not_a_dict"
        }
        mock_pulse_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        
        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=payload)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])


if __name__ == "__main__":
    unittest.main()