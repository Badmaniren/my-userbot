import unittest
import uuid
import random
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_anomaly_inspector_integration_with_pulse_engine(self):
        random_repo_id = f"repo-{uuid.uuid4()}"
        negative_metric_value = -float(random.randint(1, 100))
        high_metric_value = float(random.randint(150, 300))
        threshold_value = 100.0

        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)

        original_get_pulse = getattr(pulse_engine, "get_pulse", None)
        original_pulse = getattr(pulse_engine, "pulse", None)

        mock_payload = {
            "repo_id": random_repo_id,
            "metrics": {
                "error_rate": negative_metric_value,
                "latency_ms": high_metric_value,
                "stable_metric": 50.0
            }
        }

        if original_get_pulse:
            pulse_engine.get_pulse = lambda repo_id: mock_payload
        elif original_pulse:
            pulse_engine.pulse = lambda repo_id: mock_payload
        else:
            pulse_engine.get_pulse = lambda repo_id: mock_payload

        try:
            result = inspector.inspect(repo_id=random_repo_id, threshold=threshold_value)

            self.assertEqual(result["repo_id"], random_repo_id)
            self.assertEqual(result["status"], "inspected")
            self.assertTrue(result["is_anomaly"])
            self.assertGreater(len(result["anomalies"]), 0)
            self.assertGreater(result["deviation_score"], 0.0)

            anomaly_metrics = [a["metric"] for a in result["anomalies"]]
            self.assertIn("error_rate", anomaly_metrics)
            self.assertIn("latency_ms", anomaly_metrics)
            self.assertNotIn("stable_metric", anomaly_metrics)
        finally:
            if original_get_pulse:
                pulse_engine.get_pulse = original_get_pulse
            if original_pulse:
                pulse_engine.pulse = original_pulse

if __name__ == "__main__":
    unittest.main()