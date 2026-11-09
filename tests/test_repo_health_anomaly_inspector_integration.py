import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger


class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_inspect_integration_real_data(self):
        unique_repo_id = f"repo-{uuid.uuid4()}"
        random_threshold = float(random.randint(10, 50))
        
        negative_val = -float(random.randint(1, 10))
        high_val = random_threshold + float(random.randint(1, 20))
        normal_val = random_threshold - float(random.randint(1, 5))

        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)

        class DummyPulseEngine:
            def get_pulse(self, repo_id):
                return {
                    "repo_id": repo_id,
                    "metrics": {
                        "error_rate": negative_val,
                        "latency": high_val,
                        "cpu_load": normal_val
                    }
                }

        inspector.pulse_engine = DummyPulseEngine()

        result = inspector.inspect(
            repo_id=unique_repo_id, 
            threshold=random_threshold
        )

        self.assertEqual(result["repo_id"], unique_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertGreater(len(result["anomalies"]), 0)
        self.assertGreater(result["deviation_score"], 0.0)

        anomaly_metrics = [a["metric"] for a in result["anomalies"]]
        self.assertIn("error_rate", anomaly_metrics)
        self.assertIn("latency", anomaly_metrics)
        self.assertNotIn("cpu_load", anomaly_metrics)


if __name__ == "__main__":
    unittest.main()