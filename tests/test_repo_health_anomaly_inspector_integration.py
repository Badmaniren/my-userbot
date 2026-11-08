import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_anomaly_inspector_integration_with_pulse_engine(self):
        random_repo_id = str(uuid.uuid4())
        negative_value = -float(random.randint(1, 100))
        high_value = float(random.randint(150, 300))
        threshold_value = 100.0

        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)

        original_get_pulse = getattr(pulse_engine, "get_pulse", None)
        if original_get_pulse:
            def dynamic_get_pulse(repo_id):
                return {
                    "repo_id": repo_id,
                    "metrics": {
                        "error_rate": negative_value,
                        "latency_ms": high_value,
                        "stable_metric": 50.0
                    }
                }
            pulse_engine.get_pulse = dynamic_get_pulse

        try:
            result = inspector.inspect(
                repo_id=random_repo_id,
                threshold=threshold_value
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["repo_id"], random_repo_id)
            self.assertEqual(result["status"], "inspected")
            self.assertTrue(result["is_anomaly"])
            self.assertGreaterEqual(len(result["anomalies"]), 2)
            self.assertGreater(result["deviation_score"], 0.0)

            found_negative = False
            found_high = False
            for anomaly in result["anomalies"]:
                if anomaly["metric"] == "error_rate" and anomaly["deviation"] == "negative":
                    found_negative = True
                    self.assertEqual(anomaly["value"], negative_value)
                if anomaly["metric"] == "latency_ms" and anomaly["deviation"] == "high":
                    found_high = True
                    self.assertEqual(anomaly["value"], high_value)

            self.assertTrue(found_negative, "Отрицательная аномалия не обнаружена в интегрированном вызове")
            self.assertTrue(found_high, "Высокая аномалия выше порога не обнаружена в интегрированном вызове")

        finally:
            if original_get_pulse:
                pulse_engine.get_pulse = original_get_pulse

if __name__ == "__main__":
    unittest.main()