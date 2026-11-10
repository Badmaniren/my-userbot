import unittest
from unittest.mock import MagicMock, patch
import random
import uuid
import io

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.metric_name_neg = f"metric_neg_{uuid.uuid4().hex[:6]}"
        self.metric_name_high = f"metric_high_{uuid.uuid4().hex[:6]}"
        self.metric_name_normal = f"metric_normal_{uuid.uuid4().hex[:6]}"
        
        self.neg_value = -float(random.randint(1, 100))
        self.high_value = float(random.randint(50, 100))
        self.threshold = float(random.randint(10, 49))
        self.normal_value = float(random.randint(0, int(self.threshold)))

    def test_init_defaults(self):
        inspector = RepoHealthAnomalyInspector()
        self.assertIsNotNone(inspector.pulse_engine)
        self.assertIsNotNone(inspector.logger)

    def test_inspect_with_explicit_payload(self):
        pulse_payload = {
            "repo_id": self.repo_id,
            "metrics": {
                self.metric_name_neg: self.neg_value,
                self.metric_name_high: self.high_value,
                self.metric_name_normal: self.normal_value
            }
        }

        with patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            mock_logger = MagicMock()
            mock_logger_cls.return_value = mock_logger

            inspector = RepoHealthAnomalyInspector()
            result = inspector.inspect(repo_id=self.repo_id, pulse_payload=pulse_payload, threshold=self.threshold)

            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertEqual(result["status"], "inspected")
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 2)
            
            metrics_found = [a["metric"] for a in result["anomalies"]]
            self.assertIn(self.metric_name_neg, metrics_found)
            self.assertIn(self.metric_name_high, metrics_found)
            self.assertNotIn(self.metric_name_normal, metrics_found)

            mock_logger.info.assert_called_once()

    def test_inspect_fetches_from_pulse_engine_get_pulse(self):
        pulse_payload = {
            "repo_id": self.repo_id,
            "metrics": {
                self.metric_name_high: self.high_value
            }
        }

        mock_pulse_engine = MagicMock()
        mock_pulse_engine.get_pulse.return_value = pulse_payload

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(repo_id=self.repo_id, threshold=self.threshold)

        mock_pulse_engine.get_pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["repo_id"], self.repo_id)

    def test_inspect_fetches_from_pulse_engine_pulse(self):
        pulse_payload = {
            "repo_id": self.repo_id,
            "metrics": {
                self.metric_name_neg: self.neg_value
            }
        }

        mock_pulse_engine = MagicMock()
        del mock_pulse_engine.get_pulse
        mock_pulse_engine.pulse.return_value = pulse_payload

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(repo_id=self.repo_id)

        mock_pulse_engine.pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])

    def test_inspect_empty_payload_fallback(self):
        mock_pulse_engine = MagicMock()
        mock_pulse_engine.get_pulse.return_value = None

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(repo_id=self.repo_id)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_malformed_metrics(self):
        pulse_payload = {
            "repo_id": self.repo_id,
            "metrics": f"invalid_string_instead_of_dict_{uuid.uuid4().hex}"
        }

        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=pulse_payload)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])

    def test_strict_exception_handling_on_engine_failure(self):
        mock_pulse_engine = MagicMock()
        mock_pulse_engine.get_pulse.side_effect = RuntimeError(f"engine_crash_{uuid.uuid4().hex}")

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        
        with self.assertRaises(RuntimeError):
            inspector.inspect(repo_id=self.repo_id)


if __name__ == "__main__":
    unittest.main()