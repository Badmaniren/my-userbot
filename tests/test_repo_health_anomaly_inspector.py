import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.threshold = random.uniform(10.0, 50.0)

    def test_init_default_dependencies(self):
        inspector = RepoHealthAnomalyInspector()
        self.assertIsNotNone(inspector.pulse_engine)
        self.assertIsNotNone(inspector.logger)

    def test_inspect_with_explicit_payload(self):
        negative_val = -float(random.randint(1, 100))
        high_val = self.threshold + float(random.randint(1, 100))
        normal_val = self.threshold - 1.0

        payload = {
            "repo_id": self.repo_id,
            "metrics": {
                f"{self.metric_name}_neg": negative_val,
                f"{self.metric_name}_high": high_val,
                f"{self.metric_name}_norm": normal_val,
                f"{self.metric_name}_bool": True
            }
        }

        mock_pulse_engine = MagicMock()
        mock_logger = MagicMock()

        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine", return_value=mock_pulse_engine), \
             patch("skills.repo_health_anomaly_inspector.RepoLogger", return_value=mock_logger):
            
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
            inspector.logger = mock_logger

            result = inspector.inspect(repo_id=self.repo_id, pulse_payload=payload, threshold=self.threshold)

            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertEqual(result["status"], "inspected")
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 2)
            self.assertGreater(result["deviation_score"], 0.0)
            mock_logger.info.assert_called_once()

    def test_inspect_fetches_pulse_via_get_pulse(self):
        mock_pulse_engine = MagicMock()
        mock_pulse_engine.get_pulse.return_value = {
            "repo_id": self.repo_id,
            "metrics": {
                self.metric_name: -5.0
            }
        }
        # Удаляем метод pulse, чтобы сработал get_pulse
        if hasattr(mock_pulse_engine, "pulse"):
            del mock_pulse_engine.pulse

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(repo_id=self.repo_id)

        mock_pulse_engine.get_pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])

    def test_inspect_fetches_pulse_via_pulse_method(self):
        mock_pulse_engine = MagicMock()
        # Удаляем get_pulse
        if hasattr(mock_pulse_engine, "get_pulse"):
            del mock_pulse_engine.get_pulse
        
        mock_pulse_engine.pulse.return_value = {
            "repo_id": self.repo_id,
            "metrics": {
                self.metric_name: 100.0
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(repo_id=self.repo_id, threshold=10.0)

        mock_pulse_engine.pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])

    def test_inspect_no_anomalies_and_fallback_repo_id(self):
        mock_pulse_engine = MagicMock()
        mock_pulse_engine.get_pulse.return_value = {
            "metrics": {
                self.metric_name: 5.0
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(threshold=10.0)

        self.assertEqual(result["repo_id"], "default-repo")
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_malformed_payload_and_metrics(self):
        mock_pulse_engine = MagicMock()
        # Возвращаем невалидный payload
        mock_pulse_engine.get_pulse.return_value = "invalid_payload_string"

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=[1, 2, 3])

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])


if __name__ == "__main__":
    unittest.main()