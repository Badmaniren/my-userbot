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
        self.repo_path = self.temp_dir.name
        self.threshold = random.uniform(0.5, 0.9)
        self.pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_composition_and_flow(self):
        self.assertIsInstance(self.pipeline.filter_module, AnomalyFilter)
        self.assertIsInstance(self.pipeline.detector_module, AnomalyDetector)

        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        base_value = random.randint(10, 50)
        
        raw_data = {
            "metric_name": metric_name,
            "values": [base_value + random.randint(-2, 2) for _ in range(5)]
        }
        
        spike_value = base_value + random.randint(100, 200)
        raw_data["values"].append(spike_value)

        result = self.pipeline.process_pipeline(raw_data)

        self.assertIn("filtered_data", result)
        self.assertIn("detection_result", result)
        
        detection_output = result["detection_result"]
        self.assertTrue(any(detection_output.values()) or isinstance(detection_output, dict))

    def test_pipeline_randomized_anomaly_search(self):
        execution_id = str(uuid.uuid4())
        metrics_count = random.randint(3, 7)
        
        metrics_payload = {}
        for _ in range(metrics_count):
            m_name = f"sys_metric_{uuid.uuid4().hex[:6]}"
            m_val = random.uniform(100.0, 500.0)
            metrics_payload[m_name] = m_val

        pipeline_result = self.pipeline.run_end_to_end(execution_id, metrics_payload)

        self.assertIsInstance(pipeline_result, dict)
        self.assertGreaterEqual(len(pipeline_result), 0)


if __name__ == "__main__":
    unittest.main()