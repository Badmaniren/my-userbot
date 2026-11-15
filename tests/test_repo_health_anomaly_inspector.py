import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.rand_repo_id = f"repo-{uuid.uuid4().hex[:8]}"
        self.rand_metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        self.rand_threshold = round(random.uniform(10.0, 50.0), 2)

    def test_init_default_components(self):
        inspector = RepoHealthAnomalyInspector()
        self.assertIsNotNone(inspector.pulse_engine)
        self.assertIsNotNone(inspector.logger)

    def test_inspect_with_explicit_payload_no_anomalies(self):
        mock_pulse_engine = MagicMock()
        mock_logger = MagicMock()

        safe_val = round(random.uniform(0.1, self.rand_threshold), 2)
        payload = {
            "repo_id": self.rand_repo_id,
            "metrics": {
                self.rand_metric_name: safe_val,
                f"flag_{uuid.uuid4().hex[:4]}": True 
            }
        }

        with patch('skills.repo_health_anomaly_inspector.RepoHealthPulseEngine', return_value=mock_pulse_engine), \
             patch('skills.repo_health_anomaly_inspector.RepoLogger', return_value=mock_logger):
            
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
            inspector.logger = mock_logger
            
            result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=payload, threshold=self.rand_threshold)

            self.assertEqual(result["repo_id"], self.rand_repo_id)
            self.assertEqual(result["status"], "inspected")
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 0)
            self.assertEqual(result["deviation_score"], 0.0)
            mock_logger.info.assert_called_once()

    def test_inspect_detects_negative_anomaly(self):
        mock_pulse_engine = MagicMock()
        mock_logger = MagicMock()

        neg_val = -float(random.randint(1, 100))
        payload = {
            "metrics": {
                self.rand_metric_name: neg_val
            }
        }

        with patch('skills.repo_health_anomaly_inspector.RepoHealthPulseEngine', return_value=mock_pulse_engine), \
             patch('skills.repo_health_anomaly_inspector.RepoLogger', return_value=mock_logger):
            
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
            inspector.logger = mock_logger
            
            result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=payload)

            self.assertEqual(result["repo_id"], self.rand_repo_id)
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 1)
            self.assertEqual(result["anomalies"][0]["metric"], self.rand_metric_name)
            self.assertEqual(result["anomalies"][0]["value"], neg_val)
            self.assertEqual(result["anomalies"][0]["deviation"], "negative")
            self.assertEqual(result["deviation_score"], abs(neg_val))

    def test_inspect_detects_high_threshold_anomaly(self):
        mock_pulse_engine = MagicMock()
        mock_logger = MagicMock()

        high_val = self.rand_threshold + float(random.randint(5, 50))
        payload = {
            "metrics": {
                self.rand_metric_name: high_val
            }
        }

        with patch('skills.repo_health_anomaly_inspector.RepoHealthPulseEngine', return_value=mock_pulse_engine), \
             patch('skills.repo_health_anomaly_inspector.RepoLogger', return_value=mock_logger):
            
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
            inspector.logger = mock_logger
            
            result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=payload, threshold=self.rand_threshold)

            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 1)
            self.assertEqual(result["anomalies"][0]["deviation"], "high")
            self.assertEqual(result["deviation_score"], high_val - self.rand_threshold)

    def test_inspect_fetches_pulse_when_payload_missing(self):
        mock_pulse_engine = MagicMock()
        fetched_val = self.rand_threshold + 10.0
        mock_pulse_engine.get_pulse.return_value = {
            "repo_id": self.rand_repo_id,
            "metrics": {
                self.rand_metric_name: fetched_val
            }
        }
        mock_logger = MagicMock()

        with patch('skills.repo_health_anomaly_inspector.RepoLogger', return_value=mock_logger):
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
            inspector.logger = mock_logger
            
            result = inspector.inspect(repo_id=self.rand_repo_id, threshold=self.rand_threshold)

            mock_pulse_engine.get_pulse.assert_called_once_with(self.rand_repo_id)
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 1)

    def test_inspect_falls_back_to_pulse_method(self):
        mock_pulse_engine = MagicMock(spec=[])
        # Удаляем get_pulse, оставляем метод pulse
        del mock_pulse_engine.get_pulse
        mock_pulse_engine.pulse = MagicMock(return_value={
            "repo_id": self.rand_repo_id,
            "metrics": {
                self.rand_metric_name: -5.0
            }
        })
        mock_logger = MagicMock()

        with patch('skills.repo_health_anomaly_inspector.RepoLogger', return_value=mock_logger):
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
            inspector.logger = mock_logger
            
            result = inspector.inspect(repo_id=self.rand_repo_id)

            mock_pulse_engine.pulse.assert_called_once_with(self.rand_repo_id)
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(result["deviation_score"], 5.0)

    def test_inspect_handles_malformed_payload_and_metrics(self):
        mock_pulse_engine = MagicMock()
        mock_pulse_engine.get_pulse.return_value = "invalid_payload_string"
        mock_logger = MagicMock()

        with patch('skills.repo_health_anomaly_inspector.RepoLogger', return_value=mock_logger):
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
            inspector.logger = mock_logger
            
            # Передаем неверный тип payload и отсутствующий repo_id для проверки дефолтов
            result = inspector.inspect(repo_id=None, pulse_payload=[1, 2, 3])

            self.assertEqual(result["repo_id"], "default-repo")
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["anomalies"], [])
            self.assertEqual(result["deviation_score"], 0.0)


if __name__ == "__main__":
    unittest.main()