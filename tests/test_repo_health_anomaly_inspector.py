import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.rand_repo_id = uuid.uuid4().hex
        self.rand_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.rand_threshold = random.uniform(1.0, 50.0)

    def test_init_defaults(self):
        inspector = RepoHealthAnomalyInspector()
        self.assertIsNotNone(inspector.pulse_engine)
        self.assertIsNotNone(inspector.logger)

    def test_inspect_with_direct_payload_no_anomalies(self):
        with patch('skills.repo_logger.RepoLogger') as mock_logger_cls:
            mock_logger = MagicMock()
            mock_logger_cls.return_value = mock_logger

            inspector = RepoHealthAnomalyInspector(pulse_engine=MagicMock())
            
            payload = {
                "repo_id": self.rand_repo_id,
                "metrics": {
                    self.rand_metric_name: random.uniform(0.0, self.rand_threshold)
                }
            }

            result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=payload, threshold=self.rand_threshold)

            self.assertEqual(result["repo_id"], self.rand_repo_id)
            self.assertEqual(result["status"], "inspected")
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 0)
            self.assertEqual(result["deviation_score"], 0.0)
            mock_logger.info.assert_called_once()

    def test_inspect_with_negative_anomaly(self):
        with patch('skills.repo_logger.RepoLogger') as mock_logger_cls:
            mock_logger = MagicMock()
            mock_logger_cls.return_value = mock_logger

            inspector = RepoHealthAnomalyInspector(pulse_engine=MagicMock())
            
            neg_value = -float(random.randint(1, 100))
            payload = {
                "repo_id": self.rand_repo_id,
                "metrics": {
                    self.rand_metric_name: neg_value
                }
            }

            result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=payload)

            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 1)
            self.assertEqual(result["anomalies"][0]["metric"], self.rand_metric_name)
            self.assertEqual(result["anomalies"][0]["value"], neg_value)
            self.assertEqual(result["anomalies"][0]["deviation"], "negative")
            self.assertEqual(result["deviation_score"], abs(neg_value))

    def test_inspect_with_high_threshold_anomaly(self):
        with patch('skills.repo_logger.RepoLogger') as mock_logger_cls:
            mock_logger = MagicMock()
            mock_logger_cls.return_value = mock_logger

            inspector = RepoHealthAnomalyInspector(pulse_engine=MagicMock())
            
            high_value = self.rand_threshold + float(random.randint(1, 50))
            payload = {
                "repo_id": self.rand_repo_id,
                "metrics": {
                    self.rand_metric_name: high_value
                }
            }

            result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=payload, threshold=self.rand_threshold)

            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 1)
            self.assertEqual(result["anomalies"][0]["metric"], self.rand_metric_name)
            self.assertEqual(result["anomalies"][0]["value"], high_value)
            self.assertEqual(result["anomalies"][0]["deviation"], "high")
            self.assertEqual(result["deviation_score"], high_value - self.rand_threshold)

    def test_inspect_fetches_pulse_when_payload_is_none(self):
        with patch('skills.repo_logger.RepoLogger') as mock_logger_cls:
            mock_logger = MagicMock()
            mock_logger_cls.return_value = mock_logger

            mock_pulse_engine = MagicMock()
            fetched_payload = {
                "repo_id": self.rand_repo_id,
                "metrics": {
                    self.rand_metric_name: 0.5
                }
            }
            mock_pulse_engine.get_pulse.return_value = fetched_payload

            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
            result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=None)

            mock_pulse_engine.get_pulse.assert_called_once_with(self.rand_repo_id)
            self.assertEqual(result["repo_id"], self.rand_repo_id)
            self.assertFalse(result["is_anomaly"])

    def test_inspect_fetches_pulse_fallback_method(self):
        with patch('skills.repo_logger.RepoLogger') as mock_logger_cls:
            mock_logger = MagicMock()
            mock_logger_cls.return_value = mock_logger

            mock_pulse_engine = MagicMock(spec=[])
            fetched_payload = {
                "repo_id": self.rand_repo_id,
                "metrics": {}
            }
            mock_pulse_engine.pulse = MagicMock(return_value=fetched_payload)

            inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
            result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload="not_a_dict")

            mock_pulse_engine.pulse.assert_called_once_with(self.rand_repo_id)
            self.assertEqual(result["repo_id"], self.rand_repo_id)

    def test_inspect_handles_invalid_metrics_type(self):
        with patch('skills.repo_logger.RepoLogger') as mock_logger_cls:
            mock_logger = MagicMock()
            mock_logger_cls.return_value = mock_logger

            inspector = RepoHealthAnomalyInspector(pulse_engine=MagicMock())
            payload = {
                "repo_id": self.rand_repo_id,
                "metrics": "invalid_metrics_structure"
            }

            result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=payload)

            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["anomalies"], [])
            self.assertEqual(result["deviation_score"], 0.0)


if __name__ == "__main__":
    unittest.main()