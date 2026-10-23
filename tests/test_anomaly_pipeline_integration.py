import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_pipeline import (
    AnomalyLogger,
    AnomalyAuditHub,
    start_new,
    start_pipeline,
    ExtractorTool,
    GitInspector
)

class TestAnomalyPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_filename = f"test_anomaly_{uuid.uuid4()}.log"
        self.log_path = os.path.join(self.test_dir.name, self.log_filename)
        self.repo_path = os.path.join(self.test_dir.name, "mock_repo")
        os.makedirs(self.repo_path, exist_ok=True)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_anomaly_pipeline(self):
        rand_source = f"source_{uuid.uuid4().hex[:8]}"
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_details = f"details_{uuid.uuid4().hex}"
        rand_telemetry = {"cpu_load": random.random(), "memory": random.randint(100, 9999)}
        
        threshold = random.randint(10, 100)
        hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_path, threshold=threshold)
        
        hub.log_anomaly(rand_source, rand_severity, rand_details, rand_telemetry)
        
        self.assertTrue(os.path.exists(self.log_path), "Лог-файл должен быть создан при логировании аномалии")

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = random.uniform(0.0, 100.0)
        aggregation_result = hub.aggregate_and_report(metric_name, metric_value)
        self.assertTrue(aggregation_result, "Агрегация метрики должна завершиться успешно")

        report = hub.generate_final_report()
        self.assertIn("report_id", report)
        self.assertIn(self.log_filename, report["report_id"])
        self.assertIn("metrics", report)
        self.assertIn("anomalies", report)
        
        logged_anomalies = report["anomalies"]
        self.assertEqual(len(logged_anomalies), 1)
        self.assertEqual(logged_anomalies[0]["source"], rand_source)
        self.assertEqual(logged_anomalies[0]["severity"], rand_severity)
        self.assertEqual(logged_anomalies[0]["details"], rand_details)
        self.assertEqual(logged_anomalies[0]["telemetry"], rand_telemetry)

        pipeline_input = {"test_key": uuid.uuid4().hex}
        filtered_res = start_pipeline(pipeline_input)
        self.assertTrue(filtered_res.get("filtered"))
        self.assertEqual(filtered_res.get("test_key"), pipeline_input["test_key"])

        extractor = ExtractorTool()
        rand_tag_val = uuid.uuid4().hex[:8]
        tag_str = f'id="{rand_tag_val}" class="test-class"'
        parsed_attrs = extractor.parse_attributes(tag_str)
        self.assertEqual(parsed_attrs.get("id"), rand_tag_val)
        
        extraction_res = extractor.extract(tag_str)
        self.assertTrue(extraction_res.get("parsed"))
        self.assertEqual(extraction_res.get("markup"), tag_str)

        inspector = GitInspector(self.repo_path)
        history = inspector.get_commit_history(max_count=5)
        self.assertIsInstance(history, list)
        self.assertTrue(len(history) > 0)
        
        commit_hash = history[0].get("commit")
        file_content = inspector.read_file_at_commit(commit_hash, "any_file.py")
        self.assertIsInstance(file_content, bytes)

        repo_analysis = inspector.analyze_repository()
        self.assertIsInstance(repo_analysis, dict)
        self.assertIn("status", repo_analysis)

if __name__ == "__main__":
    unittest.main()