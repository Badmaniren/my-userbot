import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_inspect_real_integration(self):
        unique_repo_id = f"repo-{uuid.uuid4()}"
        random_threshold = round(random.uniform(5.0, 50.0), 2)
        random_high_value = random_threshold + round(random.uniform(1.0, 20.0), 2)
        random_negative_value = -round(random.uniform(1.0, 10.0), 2)

        pulse_engine = RepoHealthPulseEngine()
        logger = RepoLogger(repo_path=".")
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)
        inspector.logger = logger

        payload = {
            "repo_id": unique_repo_id,
            "metrics": {
                "cpu_load": random_high_value,
                "memory_leak_index": random_negative_value,
                "stable_metric": 1.5
            }
        }

        result = inspector.inspect(repo_id=unique_repo_id, pulse_payload=payload, threshold=random_threshold)

        self.assertEqual(result["repo_id"], unique_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertGreater(len(result["anomalies"]), 0)
        self.assertGreater(result["deviation_score"], 0.0)

        found_high = False
        found_negative = False
        for anomaly in result["anomalies"]:
            if anomaly["metric"] == "cpu_load":
                self.assertEqual(anomaly["value"], random_high_value)
                self.assertEqual(anomaly["deviation"], "high")
                found_high = True
            elif anomaly["metric"] == "memory_leak_index":
                self.assertEqual(anomaly["value"], random_negative_value)
                self.assertEqual(anomaly["deviation"], "negative")
                found_negative = True

        self.assertTrue(found_high)
        self.assertTrue(found_negative)

if __name__ == "__main__":
    unittest.main()