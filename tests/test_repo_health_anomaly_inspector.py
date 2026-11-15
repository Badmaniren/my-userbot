import unittest
from unittest.mock import patch, MagicMock
import uuid
import random

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector

class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def test_inspect_with_direct_payload_no_anomalies(self):
        rand_repo_id = uuid.uuid4().hex
        rand_metric = uuid.uuid4().hex
        rand_value = random.randint(1, 100)

        payload = {
            "repo_id": rand_repo_id,
            "metrics": {
                rand_metric: rand_value
            }
        }

        inspector = RepoHealthAnomalyInspector()
        
        with patch.object(inspector.logger, "info") as mock_logger_info:
            result = inspector.inspect(repo_id=rand_repo_id, pulse_payload=payload)

            self.assertEqual(result["repo_id"], rand_repo_id)
            self.assertEqual(result["status"], "inspected")
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["anomalies"], [])
            self.assertEqual(result["deviation_score"], 0.0)
            mock_logger_info.assert_called_once()

    def test_inspect_with_negative_anomaly(self):
        rand_repo_id = uuid.uuid4().hex
        rand_metric = uuid.uuid4().hex
        rand_value = -abs(random.randint(1, 50))

        payload = {
            "repo_id": rand_repo_id,
            "metrics": {
                rand_metric: rand_value
            }
        }

        inspector = RepoHealthAnomalyInspector()

        with patch.object(inspector.logger, "info") as mock_logger_info:
            result = inspector.inspect(repo_id=rand_repo_id, pulse_payload=payload)

            self.assertEqual(result["repo_id"], rand_repo_id)
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 1)
            self.assertEqual(result["anomalies"][0]["metric"], rand_metric)
            self.assertEqual(result["anomalies"][0]["value"], float(rand_value))
            self.assertEqual(result["anomalies"][0]["deviation"], "negative")
            self.assertEqual(result["deviation_score"], abs(float(rand_value)))
            mock_logger_info.assert_called_once()

    def test_inspect_with_threshold_anomaly(self):
        rand_repo_id = uuid.uuid4().hex
        rand_metric = uuid.uuid4().hex
        threshold_val = float(random.randint(10, 50))
        rand_value = threshold_val + float(random.randint(1, 20))

        payload = {
            "repo_id": rand_repo_id,
            "metrics": {
                rand_metric: rand_value
            }
        }

        inspector = RepoHealthAnomalyInspector()

        with patch.object(inspector.logger, "info") as mock_logger_info:
            result = inspector.inspect(repo_id=rand_repo_id, pulse_payload=payload, threshold=threshold_val)

            self.assertEqual(result["repo_id"], rand_repo_id)
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 1)
            self.assertEqual(result["anomalies"][0]["metric"], rand_metric)
            self.assertEqual(result["anomalies"][0]["value"], rand_value)
            self.assertEqual(result["anomalies"][0]["deviation"], "high")
            self.assertEqual(result["deviation_score"], rand_value - threshold_val)
            mock_logger_info.assert_called_once()

    def test_inspect_fetches_from_pulse_engine_get_pulse(self):
        rand_repo_id = uuid.uuid4().hex
        rand_metric = uuid.uuid4().hex
        rand_value = random.randint(1, 100)

        mock_engine = MagicMock()
        mock_engine.get_pulse.return_value = {
            "repo_id": rand_repo_id,
            "metrics": {
                rand_metric: rand_value
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)

        with patch.object(inspector.logger, "info") as mock_logger_info:
            result = inspector.inspect(repo_id=rand_repo_id)

            mock_engine.get_pulse.assert_called_once_with(rand_repo_id)
            self.assertEqual(result["repo_id"], rand_repo_id)
            self.assertFalse(result["is_anomaly"])
            mock_logger_info.assert_called_once()

    def test_inspect_fetches_from_pulse_engine_pulse(self):
        rand_repo_id = uuid.uuid4().hex
        rand_metric = uuid.uuid4().hex
        rand_value = random.randint(1, 100)

        mock_engine = MagicMock(spec=[])
        mock_engine.pulse = MagicMock(return_value={
            "repo_id": rand_repo_id,
            "metrics": {
                rand_metric: rand_value
            }
        })

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)

        with patch.object(inspector.logger, "info") as mock_logger_info:
            result = inspector.inspect(repo_id=rand_repo_id)

            mock_engine.pulse.assert_called_once_with(rand_repo_id)
            self.assertEqual(result["repo_id"], rand_repo_id)
            self.assertFalse(result["is_anomaly"])
            mock_logger_info.assert_called_once()

    def test_inspect_invalid_payload_defaults(self):
        rand_repo_id = uuid.uuid4().hex

        mock_engine = MagicMock()
        mock_engine.get_pulse.return_value = None

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)

        with patch.object(inspector.logger, "info") as mock_logger_info:
            result = inspector.inspect(repo_id=rand_repo_id, pulse_payload="not-a-dict")

            self.assertEqual(result["repo_id"], rand_repo_id)
            self.assertEqual(result["status"], "inspected")
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(result["anomalies"], [])
            self.assertEqual(result["deviation_score"], 0.0)
            mock_logger_info.assert_called_once()