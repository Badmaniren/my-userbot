import unittest
import uuid
import random
import tempfile
import os
from skills.anomaly_pipeline import AnomalyPipeline
from skills.anomaly_filter import AnomalyFilter
from skills.anomaly_detector import AnomalyDetector

class TestAnomalyPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.threshold = random.uniform(50.0, 100.0)

        self.detector = AnomalyDetector(
            repo_path=self.temp_dir.name,
            threshold=self.threshold,
            git_inspector=None,
            patch_verifier=None
        )
        self.filter_module = AnomalyFilter()

        self.pipeline = AnomalyPipeline(
            anomaly_filter=self.filter_module,
            anomaly_detector=self.detector
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_integration_flow(self):
        random_val_normal = random.uniform(10.0, self.threshold - 1.0)
        random_val_anomaly = random.uniform(self.threshold + 1.0, 200.0)

        raw_data = [
            {"metric": self.metric_name, "value": random_val_normal},
            {"metric": self.metric_name, "value": random_val_anomaly}
        ]

        result = self.pipeline.process(raw_data)

        self.assertIsInstance(result, dict)
        self.assertIn("filtered_data", result)
        self.assertIn("detection_results", result)

        history = self.detector.get_metric_history(self.metric_name)
        self.assertIn(random_val_normal, history)
        self.assertIn(random_val_anomaly, history)

if __name__ == "__main__":
    unittest.main()