import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger


class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def setUp(self):
        self.pulse_engine = RepoHealthPulseEngine()
        self.inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_engine)
        self.repo_id = f"repo-{uuid.uuid4()}"

    def test_inspect_integration_real_flow(self):
        random_threshold = round(random.uniform(5.0, 50.0), 2)
        random_negative_metric = round(random.uniform(-100.0, -1.0), 2)
        random_high_metric = round(random_threshold + random.uniform(1.0, 100.0), 2)

        custom_payload = {
            "repo_id": self.repo_id,
            "metrics": {
                "latency": random_negative_metric,
                "error_rate": random_high_metric,
                "normal_load": round(random.uniform(0.0, random_threshold), 2)
            }
        }

        result = self.inspector.inspect(
            repo_id=self.repo_id,
            pulse_payload=custom_payload,
            threshold=random_threshold
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), self.repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertTrue(result.get("is_anomaly"))
        
        anomalies = result.get("anomalies", [])
        self.assertGreaterEqual(len(anomalies), 2)
        
        found_negative = False
        found_high = False
        for anomaly in anomalies:
            if anomaly.get("metric") == "latency" and anomaly.get("value") == random_negative_metric:
                found_negative = True
            if anomaly.get("metric") == "error_rate" and anomaly.get("value") == random_high_metric:
                found_high = True

        self.assertTrue(found_negative, "Отрицательная аномалия не обнаружена в реальном потоке данных")
        self.assertTrue(found_high, "Аномалия превышения порога не обнаружена в реальном потоке данных")
        self.assertGreater(result.get("deviation_score", 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()