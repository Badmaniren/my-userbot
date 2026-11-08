import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_inspect_integration_real_pulse_engine(self):
        random_repo_id = str(uuid.uuid4())
        negative_val = -float(random.randint(1, 100))
        high_val = float(random.randint(150, 300))
        threshold_val = 100.0

        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)

        result = inspector.inspect(
            repo_id=random_repo_id,
            threshold=threshold_val
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), random_repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertIn("is_anomaly", result)
        self.assertIn("anomalies", result)
        self.assertIn("deviation_score", result)
        self.assertIsInstance(result.get("anomalies"), list)
        self.assertIsInstance(result.get("deviation_score"), float)

if __name__ == "__main__":
    unittest.main()