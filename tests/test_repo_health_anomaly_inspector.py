import unittest
from unittest.mock import MagicMock, patch
import uuid
import random

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.pulse_engine_mock = MagicMock()
        self.inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_engine_mock)
        self.repo_id = uuid.uuid4().hex

    def test_inspect_with_explicit_pulse_payload_and_negative_metrics(self):
        metric_name = uuid.uuid4().hex
        neg_val = -float(random.randint(1, 100))
        payload = {
            "metrics": {
                metric_name: neg_val
            }
        }
        
        result = self.inspector.inspect(self.repo_id, pulse_payload=payload)
        
        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], metric_name)
        self.assertEqual(result["anomalies"][0]["value"], neg_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")
        self.assertEqual(result["deviation_score"], abs(neg_val))

    def test_inspect_fetches_pulse_via_get_pulse_when_payload_is_none(self):
        metric_name = uuid.uuid4().hex
        high_val = float(random.randint(101, 200))
        threshold = 50.0
        
        self.pulse_engine_mock.get_pulse.return_value = {
            "metrics": {
                metric_name: high_val
            }
        }
        
        result = self.inspector.inspect(self.repo_id, threshold=threshold)
        
        self.pulse_engine_mock.get_pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["anomalies"][0]["deviation"], "high")
        self.assertEqual(result["deviation_score"], high_val - threshold)

    def test_inspect_fetches_pulse_via_pulse_method_fallback(self):
        del self.pulse_engine_mock.get_pulse
        metric_name = uuid.uuid4().hex
        val = -float(random.randint(1, 50))
        
        self.pulse_engine_mock.pulse.return_value = {
            "metrics": {
                metric_name: val
            }
        }
        
        result = self.inspector.inspect(self.repo_id)
        
        self.pulse_engine_mock.pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])

    def test_inspect_handles_none_payload_gracefully(self):
        self.pulse_engine_mock.get_pulse.return_value = None
        
        result = self.inspector.inspect(self.repo_id, pulse_payload=None)
        
        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_ignores_non_numeric_metric_values(self):
        valid_metric = uuid.uuid4().hex
        valid_val = float(random.randint(1, 10))
        invalid_metric = uuid.uuid4().hex
        invalid_val = uuid.uuid4().hex
        
        payload = {
            "metrics": {
                valid_metric: valid_val,
                invalid_metric: invalid_val,
                uuid.uuid4().hex: True
            }
        }
        
        result = self.inspector.inspect(self.repo_id, pulse_payload=payload, threshold=0.5)
        
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], valid_metric)


if __name__ == "__main__":
    unittest.main()