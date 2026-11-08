import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_inspect_integration_real_pulse_engine(self):
        random_repo_id = str(uuid.uuid4())
        random_threshold = float(random.randint(5, 50))
        
        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)
        
        result = inspector.inspect(repo_id=random_repo_id, threshold=random_threshold)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), random_repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertIn("is_anomaly", result)
        self.assertIn("anomalies", result)
        self.assertIn("deviation_score", result)
        
        anomalies = result.get("anomalies")
        self.assertIsInstance(anomalies, list)
        
        for anomaly in anomalies:
            self.assertIn("metric", anomaly)
            self.assertIn("value", anomaly)
            self.assertIn("deviation", anomaly)
            value = anomaly.get("value")
            self.assertTrue(value < 0 or value > random_threshold)

if __name__ == "__main__":
    unittest.main()