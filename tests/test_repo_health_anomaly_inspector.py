import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.rand_repo_id = uuid.uuid4().hex
        self.rand_metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.mock_pulse_engine = MagicMock()

    def test_init_defaults(self):
        inspector = RepoHealthAnomalyInspector()
        self.assertIsNotNone(inspector.pulse_engine)
        self.assertIsNotNone(inspector.logger)

    def test_inspect_with_explicit_payload_and_threshold(self):
        inspector = RepoHealthAnomalyInspector(pulse_engine=self.mock_pulse_engine)
        
        bad_val = -float(random.randint(1, 100))
        high_val = float(random.randint(101, 200))
        threshold_val = 50.0

        payload = {
            "repo_id": self.rand_repo_id,
            "metrics": {
                f"{self.rand_metric_name}_neg": bad_val,
                f"{self.rand_metric_name}_high": high_val,
                f"{self.rand_metric_name}_normal": 10.0,
                f"{self.rand_metric_name}_bool": True
            }
        }

        result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=payload, threshold=threshold_val)

        self.assertEqual(result["repo_id"], self.rand_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 2)
        
        found_negative = False
        found_high = False
        for anomaly in result["anomalies"]:
            if anomaly["deviation"] == "negative":
                self.assertEqual(anomaly["value"], bad_val)
                found_negative = True
            elif anomaly["deviation"] == "high":
                self.assertEqual(anomaly["value"], high_val)
                found_high = True

        self.assertTrue(found_negative)
        self.assertTrue(found_high)
        self.assertGreater(result["deviation_score"], 0.0)
        self.mock_pulse_engine.get_pulse.assert_not_called()

    def test_inspect_fetches_pulse_via_get_pulse(self):
        inspector = RepoHealthAnomalyInspector(pulse_engine=self.mock_pulse_engine)
        
        normal_val = float(random.randint(1, 40))
        payload = {
            "repo_id": self.rand_repo_id,
            "metrics": {
                self.rand_metric_name: normal_val
            }
        }
        self.mock_pulse_engine.get_pulse.return_value = payload

        result = inspector.inspect(repo_id=self.rand_repo_id, threshold=100.0)

        self.mock_pulse_engine.get_pulse.assert_called_once_with(self.rand_repo_id)
        self.assertEqual(result["repo_id"], self.rand_repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_fetches_pulse_via_pulse_method(self):
        del self.mock_pulse_engine.get_pulse
        self.mock_pulse_engine.pulse = MagicMock()
        
        inspector = RepoHealthAnomalyInspector(pulse_engine=self.mock_pulse_engine)
        
        payload = {
            "repo_id": self.rand_repo_id,
            "metrics": {}
        }
        self.mock_pulse_engine.pulse.return_value = payload

        result = inspector.inspect(repo_id=self.rand_repo_id)

        self.mock_pulse_engine.pulse.assert_called_once_with(self.rand_repo_id)
        self.assertEqual(result["repo_id"], self.rand_repo_id)

    def test_inspect_malformed_payloads(self):
        inspector = RepoHealthAnomalyInspector(pulse_engine=self.mock_pulse_engine)
        
        # Test pulse_payload as non-dict
        with patch.object(self.mock_pulse_engine, 'get_pulse', return_value="invalid_payload_string"):
            result = inspector.inspect(repo_id=self.rand_repo_id)
            self.assertEqual(result["repo_id"], self.rand_repo_id)
            self.assertFalse(result["is_anomaly"])

        # Test metrics as non-dict
        payload = {
            "repo_id": self.rand_repo_id,
            "metrics": "not_a_dict"
        }
        result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=payload)
        self.assertEqual(result["repo_id"], self.rand_repo_id)
        self.assertFalse(result["is_anomaly"])

    def test_inspect_default_repo_id_fallback(self):
        inspector = RepoHealthAnomalyInspector(pulse_engine=self.mock_pulse_engine)
        payload = {
            "metrics": {}
        }
        result = inspector.inspect(repo_id=None, pulse_payload=payload)
        self.assertEqual(result["repo_id"], "default-repo")

        result_empty = inspector.inspect(repo_id=None, pulse_payload=None)
        self.assertEqual(result_empty["repo_id"], "default-repo")