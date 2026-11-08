import unittest
from unittest.mock import patch
import uuid
import random
import string
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.random_metric = "".join(random.choices(string.ascii_lowercase, k=8))

    def test_init_default_engine_and_logger(self):
        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine") as mock_engine_cls, \
             patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            
            inspector = RepoHealthAnomalyInspector()
            self.assertIsNotNone(inspector.pulse_engine)
            self.assertIsNotNone(inspector.logger)
            mock_engine_cls.assert_called_once()

    def test_init_custom_engine(self):
        custom_engine = unittest.mock.MagicMock()
        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)
            self.assertEqual(inspector.pulse_engine, custom_engine)

    def test_inspect_with_explicit_pulse_payload(self):
        negative_val = -float(random.randint(1, 100))
        high_val = float(random.randint(105, 200))
        threshold = 100.0

        payload = {
            "metrics": {
                f"{self.random_metric}_neg": negative_val,
                f"{self.random_metric}_high": high_val,
                f"{self.random_metric}_normal": 50.0
            }
        }

        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector()
            result = inspector.inspect(repo_id=self.repo_id, pulse_payload=payload, threshold=threshold)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 2)
        
        expected_deviation_score = abs(negative_val) + (high_val - threshold)
        self.assertAlmostEqual(result["deviation_score"], expected_deviation_score)

    def test_inspect_fetches_pulse_via_get_pulse(self):
        mock_engine = unittest.mock.MagicMock()
        negative_val = -float(random.randint(1, 50))
        mock_engine.get_pulse.return_value = {
            "metrics": {
                self.random_metric: negative_val
            }
        }
        del mock_engine.pulse

        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
            result = inspector.inspect(repo_id=self.repo_id)

        mock_engine.get_pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["anomalies"][0]["metric"], self.random_metric)
        self.assertEqual(result["anomalies"][0]["value"], negative_val)

    def test_inspect_fetches_pulse_via_pulse_method(self):
        mock_engine = unittest.mock.MagicMock()
        del mock_engine.get_pulse
        normal_val = float(random.randint(1, 10))
        mock_engine.pulse.return_value = {
            "metrics": {
                self.random_metric: normal_val
            }
        }

        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
            result = inspector.inspect(repo_id=self.repo_id, threshold=100.0)

        mock_engine.pulse.assert_called_once_with(self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_fallback_empty_pulse(self):
        mock_engine = unittest.mock.MagicMock()
        if hasattr(mock_engine, "get_pulse"):
            del mock_engine.get_pulse
        if hasattr(mock_engine, "pulse"):
            del mock_engine.pulse

        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
            result = inspector.inspect(repo_id=self.repo_id)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_pulse_payload_is_none_fallback(self):
        mock_engine = unittest.mock.MagicMock()
        mock_engine.get_pulse.return_value = None

        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
            result = inspector.inspect(repo_id=self.repo_id, pulse_payload=None)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["deviation_score"], 0.0)


if __name__ == "__main__":
    unittest.main()