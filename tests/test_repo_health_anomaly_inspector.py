import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.random_repo_id = uuid.uuid4().hex
        self.random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))

    def test_init_default_dependencies(self):
        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine") as mock_engine_cls, \
             patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            
            inspector = RepoHealthAnomalyInspector()
            
            mock_engine_cls.assert_called_once()
            mock_logger_cls.assert_called_once_with(repo_path=".")
            self.assertIsNotNone(inspector.pulse_engine)
            self.assertIsNotNone(inspector.logger)

    def test_inspect_with_explicit_payload_no_anomalies(self):
        mock_engine = MagicMock()
        mock_logger = MagicMock()

        rand_val = random.uniform(0.0, 50.0)
        payload = {
            "repo_id": self.random_repo_id,
            "metrics": {
                self.random_metric_name: rand_val
            }
        }

        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine", return_value=mock_engine), \
             patch("skills.repo_health_anomaly_inspector.RepoLogger", return_value=mock_logger):
            
            inspector = RepoHealthAnomalyInspector()
            result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload=payload, threshold=100.0)

            self.assertEqual(result["repo_id"], self.random_repo_id)
            self.assertEqual(result["status"], "inspected")
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["anomalies"], [])
            self.assertEqual(result["deviation_score"], 0.0)
            mock_logger.info.assert_called_once()

    def test_inspect_negative_anomaly_detection(self):
        mock_engine = MagicMock()
        mock_logger = MagicMock()

        negative_val = -float(random.randint(1, 100))
        payload = {
            "repo_id": self.random_repo_id,
            "metrics": {
                self.random_metric_name: negative_val
            }
        }

        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine", return_value=mock_engine), \
             patch("skills.repo_health_anomaly_inspector.RepoLogger", return_value=mock_logger):
            
            inspector = RepoHealthAnomalyInspector()
            result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload=payload)

            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 1)
            self.assertEqual(result["anomalies"][0]["metric"], self.random_metric_name)
            self.assertEqual(result["anomalies"][0]["value"], negative_val)
            self.assertEqual(result["anomalies"][0]["deviation"], "negative")
            self.assertEqual(result["deviation_score"], abs(negative_val))

    def test_inspect_high_threshold_anomaly_detection(self):
        mock_engine = MagicMock()
        mock_logger = MagicMock()

        threshold = float(random.randint(10, 50))
        high_val = threshold + float(random.randint(1, 50))
        payload = {
            "repo_id": self.random_repo_id,
            "metrics": {
                self.random_metric_name: high_val
            }
        }

        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine", return_value=mock_engine), \
             patch("skills.repo_health_anomaly_inspector.RepoLogger", return_value=mock_logger):
            
            inspector = RepoHealthAnomalyInspector()
            result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload=payload, threshold=threshold)

            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 1)
            self.assertEqual(result["anomalies"][0]["metric"], self.random_metric_name)
            self.assertEqual(result["anomalies"][0]["value"], high_val)
            self.assertEqual(result["anomalies"][0]["deviation"], "high")
            self.assertEqual(result["deviation_score"], high_val - threshold)

    def test_inspect_fetches_pulse_via_get_pulse(self):
        mock_engine = MagicMock()
        payload = {
            "repo_id": self.random_repo_id,
            "metrics": {
                self.random_metric_name: 10.0
            }
        }
        mock_engine.get_pulse.return_value = payload
        if hasattr(mock_engine, "pulse"):
            delattr(mock_engine, "pulse")

        with patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            mock_logger = mock_logger_cls.return_value
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
            
            result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload=None)

            mock_engine.get_pulse.assert_called_once_with(self.random_repo_id)
            self.assertEqual(result["repo_id"], self.random_repo_id)

    def test_inspect_fetches_pulse_via_pulse_method(self):
        mock_engine = MagicMock()
        payload = {
            "repo_id": self.random_repo_id,
            "metrics": {}
        }
        if hasattr(mock_engine, "get_pulse"):
            delattr(mock_engine, "get_pulse")
        mock_engine.pulse.return_value = payload

        with patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            mock_logger = mock_logger_cls.return_value
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
            
            result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload=None)

            mock_engine.pulse.assert_called_once_with(self.random_repo_id)
            self.assertEqual(result["repo_id"], self.random_repo_id)

    def test_inspect_handles_invalid_pulse_payload(self):
        mock_engine = MagicMock()
        mock_engine.get_pulse.return_value = None

        with patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            mock_logger = mock_logger_cls.return_value
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
            
            result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload="not_a_dict")

            self.assertEqual(result["repo_id"], self.random_repo_id)
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["anomalies"], [])

    def test_inspect_ignores_non_numeric_or_boolean_metrics(self):
        mock_engine = MagicMock()
        invalid_metric_name = ''.join(random.choices(string.ascii_lowercase, k=6))
        payload = {
            "repo_id": self.random_repo_id,
            "metrics": {
                invalid_metric_name: True,
                "another_invalid": "string_value",
                "nested": {"sub": 123}
            }
        }

        with patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
            result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload=payload)

            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["anomalies"], [])
            self.assertEqual(result["deviation_score"], 0.0)