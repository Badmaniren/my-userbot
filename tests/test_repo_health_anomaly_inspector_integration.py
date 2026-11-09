import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger


class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):

    def test_inspect_integration_real_chain(self):
        unique_repo_id = f"repo-{uuid.uuid4()}"
        random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        
        negative_value = -float(random.randint(1, 100))
        high_value = float(random.randint(150, 300))
        threshold_val = 100.0

        pulse_engine = RepoHealthPulseEngine()
        logger = RepoLogger(repo_path=".")
        
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)
        inspector.logger = logger

        custom_payload = {
            "metrics": {
                random_metric_name: negative_value,
                "stable_metric": 42.0,
                "overflow_metric": high_value
            }
        }

        result = inspector.inspect(
            repo_id=unique_repo_id,
            pulse_payload=custom_payload,
            threshold=threshold_val
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["repo_id"], unique_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        
        found_metrics = [anomaly["metric"] for anomaly in result["anomalies"]]
        self.assertIn(random_metric_name, found_metrics)
        self.assertIn("overflow_metric", found_metrics)
        
        expected_deviation = abs(negative_value) + (high_value - threshold_val)
        self.assertAlmostEqual(result["deviation_score"], expected_deviation)


if __name__ == "__main__":
    unittest.main()