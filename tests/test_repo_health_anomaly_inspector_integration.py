import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_inspect_real_integration_flow(self):
        unique_repo_id = f"repo-{uuid.uuid4()}"
        random_threshold = float(random.randint(50, 100))
        
        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)
        
        # Передаем реальные динамические данные для проверки интеграции без моков
        dynamic_payload = {
            "repo_id": unique_repo_id,
            "metrics": {
                "cpu_load": -15.5,
                "memory_leak_rate": random_threshold + 25.0,
                "stable_metric": 42.0
            }
        }
        
        result = inspector.inspect(
            repo_id=unique_repo_id, 
            pulse_payload=dynamic_payload, 
            threshold=random_threshold
        )
        
        self.assertEqual(result["repo_id"], unique_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertGreaterEqual(len(result["anomalies"]), 2)
        self.assertGreater(result["deviation_score"], 0.0)

if __name__ == "__main__":
    unittest.main()