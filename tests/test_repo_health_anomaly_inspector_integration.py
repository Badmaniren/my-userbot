import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_inspect_integration_real_chain(self):
        random_repo_id = str(uuid.uuid4())
        random_threshold = round(random.uniform(5.0, 50.0), 2)
        
        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)
        
        result = inspector.inspect(repo_id=random_repo_id, threshold=random_threshold)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["repo_id"], random_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertIn("is_anomaly", result)
        self.assertIn("anomalies", result)
        self.assertIn("deviation_score", result)
        self.assertIsInstance(result["anomalies"], list)
        self.assertIsInstance(result["deviation_score"], (int, float))

if __name__ == "__main__":
    unittest.main()