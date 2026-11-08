import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.inspector = RepoHealthAnomalyInspector()

    def test_inspect_with_direct_payload_metrics(self):
        metric_key = str(uuid.uuid4())
        negative_val = -1 * random.randint(1, 100)
        payload = {
            "metrics": {
                metric_key: negative_val
            }
        }
        
        result = self.inspector.inspect(self.repo_id, pulse_payload=payload)
        
        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], metric_key)
        self.assertEqual(result["anomalies"][0]["value"], negative_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")

    def test_inspect_with_pulse_engine_fallback(self):
        mock_engine = MagicMock()
        metric_key = str(uuid.uuid4())
        normal_val = random.randint(10, 100)
        mock_engine.get_metrics.return_value = {metric_key: normal_val}

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.repo_id)

        mock_engine.get_metrics.assert_called_once_with(self.repo_id)
        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["status"], "inspected")

    def test_inspect_with_threshold_deviation(self):
        metric_key = str(uuid.uuid4())
        metric_val = random.randint(1, 50)
        threshold_val = metric_val + random.randint(10, 50)
        
        payload = {
            "metrics": {
                metric_key: metric_val
            }
        }
        
        result = self.inspector.inspect(self.repo_id, pulse_payload=payload, threshold=threshold_val)
        
        self.assertTrue(result["is_anomaly"])
        self.assertGreater(result["deviation_score"], 0.0)

    def test_inspect_pulse_engine_type_error_handling(self):
        mock_engine = MagicMock()
        mock_engine.get_metrics.side_effect = TypeError("Unexpected signature")

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.repo_id)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])