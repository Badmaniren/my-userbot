import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):
    def setUp(self):
        self.random_repo_id = uuid.uuid4().hex
        self.random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))

    def test_init_default_engines(self):
        inspector = RepoHealthAnomalyInspector()
        self.assertIsNotNone(inspector.pulse_engine)
        self.assertIsNotNone(inspector.logger)

    def test_init_custom_pulse_engine(self):
        custom_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)
        self.assertEqual(inspector.pulse_engine, custom_engine)

    def test_inspect_with_explicit_repo_and_payload(self):
        negative_val = -float(random.randint(1, 100))
        payload = {
            "metrics": {
                self.random_metric_name: negative_val
            }
        }
        
        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload=payload)

        self.assertEqual(result["repo_id"], self.random_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.random_metric_name)
        self.assertEqual(result["anomalies"][0]["value"], negative_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")
        self.assertEqual(result["deviation_score"], abs(negative_val))

    def test_inspect_repo_id_extraction_from_payload(self):
        payload = {
            "repo_id": self.random_repo_id,
            "metrics": {}
        }
        
        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(pulse_payload=payload)

        self.assertEqual(result["repo_id"], self.random_repo_id)

    def test_inspect_default_repo_id_fallback(self):
        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(repo_id=None, pulse_payload=None)

        self.assertEqual(result["repo_id"], "default-repo")

    def test_inspect_calls_pulse_engine_get_pulse(self):
        mock_engine = MagicMock()
        mock_engine.get_pulse.return_value = {
            "metrics": {
                self.random_metric_name: 0.0
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload=None)

        mock_engine.get_pulse.assert_called_once_with(self.random_repo_id)
        self.assertFalse(result["is_anomaly"])

    def test_inspect_calls_pulse_engine_pulse_fallback(self):
        mock_engine = MagicMock(spec=[])
        mock_engine.pulse = MagicMock(return_value={
            "metrics": {
                self.random_metric_name: -5.5
            }
        })

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload=None)

        mock_engine.pulse.assert_called_once_with(self.random_repo_id)
        self.assertTrue(result["is_anomaly"])

    def test_inspect_threshold_violation(self):
        threshold_val = float(random.randint(10, 50))
        high_val = threshold_val + float(random.randint(1, 20))
        
        payload = {
            "metrics": {
                self.random_metric_name: high_val
            }
        }

        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload=payload, threshold=threshold_val)

        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["deviation"], "high")
        self.assertAlmostEqual(result["deviation_score"], high_val - threshold_val)

    def test_inspect_ignores_invalid_metrics_types(self):
        payload = {
            "metrics": {
                "bool_metric": True,
                "string_metric": uuid.uuid4().hex,
                "none_metric": None,
                "dict_metric": {},
                self.random_metric_name: float(random.randint(1, 10))
            }
        }

        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload=payload, threshold=0.5)

        # Only the numeric one could be an anomaly if it exceeds threshold
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.random_metric_name)

    def test_inspect_malformed_payload_types(self):
        inspector = RepoHealthAnomalyInspector()
        
        # Non-dict pulse_payload should fallback gracefully
        result = inspector.inspect(repo_id=self.random_repo_id, pulse_payload="not_a_dict")
        self.assertEqual(result["repo_id"], self.random_repo_id)
        self.assertFalse(result["is_anomaly"])

        # Metrics not a dict
        result2 = inspector.inspect(repo_id=self.random_repo_id, pulse_payload={"metrics": [1, 2, 3]})
        self.assertFalse(result2["is_anomaly"])


if __name__ == "__main__":
    unittest.main()