import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_inspect_end_to_end_real_pulse_engine(self):
        repo_id = str(uuid.uuid4())
        
        real_pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=real_pulse_engine)
        
        random_threshold = random.uniform(5.0, 50.0)
        
        result = inspector.inspect(repo_id=repo_id, threshold=random_threshold)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertIn("is_anomaly", result)
        self.assertIn("anomalies", result)
        self.assertIn("deviation_score", result)
        self.assertIsInstance(result.get("anomalies"), list)
        self.assertIsInstance(result.get("deviation_score"), float)

if __name__ == "__main__":
    unittest.main()