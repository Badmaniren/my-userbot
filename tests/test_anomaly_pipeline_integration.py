import os
import random
import shutil
import tempfile
import unittest
import uuid

from skills.anomaly_pipeline import AnomalyPipeline, AnomalyPipelineError


class TestAnomalyPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_pipeline_")
        self.threshold = round(random.uniform(1.5, 4.0), 2)
        self.pipeline = AnomalyPipeline(repo_path=self.test_dir, threshold=self.threshold)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pipeline_initialization(self):
        self.assertIsNotNone(self.pipeline)
        self.assertEqual(self.pipeline.repo_path, self.test_dir)
        self.assertEqual(self.pipeline.threshold, self.threshold)

    def test_run_single_metric_flow(self):
        metric_name = f"cpu_metric_{uuid.uuid4().hex[:8]}"
        target_value = round(random.uniform(10.0, 95.0), 2)
        payload = {metric_name: target_value}

        result = self.pipeline.run(payload)

        self.assertIsInstance(result, dict)
        self.assertIn("is_anomaly", result)
        self.assertEqual(result.get("metric_name"), metric_name)
        self.assertEqual(result.get("target_value"), target_value)
        self.assertIsInstance(result["is_anomaly"], bool)

    def test_run_empty_input(self):
        result = self.pipeline.run({})
        self.assertIsInstance(result, dict)
        self.assertIn("is_anomaly", result)
        self.assertFalse(result["is_anomaly"])

    def test_run_batch_metrics(self):
        metrics_count = random.randint(3, 5)
        batch_data = {
            f"metric_{uuid.uuid4().hex[:6]}_{i}": round(random.uniform(5.0, 100.0), 3)
            for i in range(metrics_count)
        }

        results = self.pipeline.run_batch(batch_data)

        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), len(batch_data))
        for metric_key in batch_data:
            self.assertIn(metric_key, results)
            self.assertIsInstance(results[metric_key], bool)

    def test_process_pipeline_scalar_and_list_values(self):
        scalar_metric = f"ram_usage_{uuid.uuid4().hex[:6]}"
        scalar_value = round(random.uniform(20.0, 80.0), 2)
        list_metric = f"latency_samples_{uuid.uuid4().hex[:6]}"
        list_values = [round(random.uniform(100.0, 300.0), 1) for _ in range(3)]

        raw_data = {
            scalar_metric: scalar_value,
            list_metric: list_values,
        }

        output = self.pipeline.process_pipeline(raw_data)

        self.assertIsInstance(output, dict)
        self.assertIn("filtered_data", output)
        self.assertIn("detection_result", output)
        self.assertEqual(output["filtered_data"][scalar_metric], scalar_value)
        self.assertEqual(output["filtered_data"][list_metric], list_values)
        self.assertIn(scalar_metric, output["detection_result"])
        self.assertIn(list_metric, output["detection_result"])
        self.assertIsInstance(output["detection_result"][scalar_metric], bool)
        self.assertIsInstance(output["detection_result"][list_metric], bool)

    def test_run_end_to_end_flow(self):
        execution_id = f"exec_{uuid.uuid4()}"
        metrics_payload = {
            f"disk_io_{uuid.uuid4().hex[:8]}": round(random.uniform(1.0, 50.0), 2),
            f"net_traffic_{uuid.uuid4().hex[:8]}": round(random.uniform(100.0, 1000.0), 2),
        }

        results = self.pipeline.run_end_to_end(execution_id, metrics_payload)

        self.assertIsInstance(results, dict)
        self.assertEqual(set(results.keys()), set(metrics_payload.keys()))
        for m_name in metrics_payload:
            self.assertIsInstance(results[m_name], bool)


if __name__ == "__main__":
    unittest.main()