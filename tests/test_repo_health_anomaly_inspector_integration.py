import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_inspect_real_integration_flow(self):
        random_repo_id = str(uuid.uuid4())
        
        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)
        
        negative_val = -float(random.randint(1, 100))
        normal_val = float(random.randint(50, 200))
        
        payload_metrics = {
            "error_rate": negative_val,
            "latency_ms": normal_val
        }
        
        pulse_payload = {
            "metrics": payload_metrics
        }
        
        threshold = 10.0
        
        result = inspector.inspect(
            repo_id=random_repo_id, 
            pulse_payload=pulse_payload, 
            threshold=threshold
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), random_repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertTrue(result.get("is_anomaly"))
        
        anomalies = result.get("anomalies", [])
        self.assertTrue(len(anomalies) > 0)
        
        found_negative = False
        for anomaly in anomalies:
            if anomaly.get("metric") == "error_rate":
                self.assertEqual(anomaly.get("value"), negative_val)
                self.assertEqual(anomaly.get("deviation"), "negative")
                found_negative = True
                
        self.assertTrue(found_negative)
        self.assertGreater(result.get("deviation_score", 0.0), 0.0)

if __name__ == "__main__":
    unittest.main()