import random
import unittest
import uuid

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine


class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):

    def setUp(self):
        self.pulse_engine = RepoHealthPulseEngine()
        self.inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_engine)

    def test_inspect_integration_with_pulse_engine(self):
        random_repo_id = f"repo-pulse-{uuid.uuid4().hex}"
        result = self.inspector.inspect(repo_id=random_repo_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "inspected")
        self.assertEqual(result["repo_id"], random_repo_id)
        self.assertIn("is_anomaly", result)
        self.assertIsInstance(result["anomalies"], list)
        self.assertIsInstance(result["deviation_score"], float)

    def test_inspect_detection_and_score_calculation(self):
        random_repo_id = f"repo-anomaly-{uuid.uuid4().hex}"
        threshold = round(random.uniform(10.0, 50.0), 2)

        metric_neg = f"metric_neg_{uuid.uuid4().hex[:6]}"
        metric_high = f"metric_high_{uuid.uuid4().hex[:6]}"
        metric_normal = f"metric_ok_{uuid.uuid4().hex[:6]}"

        neg_val = -round(random.uniform(1.0, 25.0), 2)
        high_val = threshold + round(random.uniform(5.0, 40.0), 2)
        normal_val = round(random.uniform(0.0, threshold - 0.5), 2)

        payload = {
            "repo_id": random_repo_id,
            "metrics": {
                metric_neg: neg_val,
                metric_high: high_val,
                metric_normal: normal_val,
            },
        }

        result = self.inspector.inspect(
            repo_id=random_repo_id, pulse_payload=payload, threshold=threshold
        )

        expected_deviation = abs(neg_val) + (high_val - threshold)

        self.assertEqual(result["repo_id"], random_repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 2)
        self.assertAlmostEqual(result["deviation_score"], expected_deviation, places=4)

        anomalies_map = {a["metric"]: a for a in result["anomalies"]}

        self.assertIn(metric_neg, anomalies_map)
        self.assertEqual(anomalies_map[metric_neg]["deviation"], "negative")
        self.assertEqual(anomalies_map[metric_neg]["value"], float(neg_val))

        self.assertIn(metric_high, anomalies_map)
        self.assertEqual(anomalies_map[metric_high]["deviation"], "high")
        self.assertEqual(anomalies_map[metric_high]["value"], float(high_val))

    def test_inspect_clean_metrics_no_anomalies(self):
        random_repo_id = f"repo-clean-{uuid.uuid4().hex}"
        threshold = 100.0
        metric_clean = f"metric_val_{uuid.uuid4().hex[:6]}"
        clean_val = round(random.uniform(1.0, 50.0), 2)

        payload = {
            "repo_id": random_repo_id,
            "metrics": {
                metric_clean: clean_val,
            },
        }

        result = self.inspector.inspect(
            repo_id=random_repo_id, pulse_payload=payload, threshold=threshold
        )

        self.assertEqual(result["repo_id"], random_repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 0)
        self.assertEqual(result["deviation_score"], 0.0)


if __name__ == "__main__":
    unittest.main()