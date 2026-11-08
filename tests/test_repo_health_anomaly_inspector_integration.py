import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.pulse_engine = RepoHealthPulseEngine()
        self.inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_engine)

    def test_anomaly_inspector_real_integration(self):
        random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        negative_value = -float(random.randint(1, 100))
        high_value = float(random.randint(150, 300))
        threshold = 100.0

        custom_payload = {
            "metrics": {
                random_metric_name: negative_value,
                "stable_metric": 42.0,
                "spike_metric": high_value
            }
        }

        result = self.inspector.inspect(
            repo_id=self.repo_id,
            pulse_payload=custom_payload,
            threshold=threshold
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), self.repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertTrue(result.get("is_anomaly"))
        
        anomalies = result.get("anomalies", [])
        self.assertGreaterEqual(len(anomalies), 2)

        anomaly_metrics = [a["metric"] for a in anomalies]
        self.assertIn(random_metric_name, anomaly_metrics)
        self.assertIn("spike_metric", anomaly_metrics)
        self.assertGreater(result.get("deviation_score", 0.0), 0.0)

    def test_anomaly_inspector_implicit_pulse_integration(self):
        result = self.inspector.inspect(repo_id=self.repo_id)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), self.repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertIn("is_anomaly", result)
        self.assertIn("anomalies", result)
        self.assertIn("deviation_score", result)

if __name__ == "__main__":
    unittest.main()