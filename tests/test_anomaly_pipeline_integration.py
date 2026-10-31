import unittest
import os
import uuid
import random
from skills.anomaly_pipeline import AnomalyLogger, AnomalyAuditHub, start_pipeline, ExtractorTool, GitInspector

class TestAnomalyPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = str(uuid.uuid4())
        self.log_path = f"test_anomaly_{self.unique_id}.log"
        self.repo_path = f"/mock/repo/{self.unique_id}"
        self.threshold = round(random.uniform(0.1, 0.9), 2)
        
        self.logger = AnomalyLogger(self.log_path)
        self.logger.clear_logs()
        
        self.hub = AnomalyAuditHub(self.repo_path, self.log_path, self.threshold)
        self.extractor = ExtractorTool()
        self.inspector = GitInspector(self.repo_path)

    def tearDown(self):
        if os.path.exists(self.log_path):
            try:
                os.remove(self.log_path)
            except OSError:
                pass

    def test_pipeline_telemetry_integration(self):
        source_name = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_msg = f"Random anomaly detail: {uuid.uuid4()}"
        telemetry_data = {
            "cpu_load": random.randint(10, 100),
            "memory_usage": round(random.uniform(1.0, 16.0), 2),
            "active_threads": random.randint(1, 50)
        }

        self.hub.log_anomaly(source_name, severity_level, details_msg, telemetry_data)
        
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_val = random.randint(100, 999)
        aggregation_result = self.hub.aggregate_and_report(metric_name, metric_val)
        self.assertTrue(aggregation_result)

        tag_key = f"key_{uuid.uuid4().hex[:4]}"
        tag_val = f"val_{uuid.uuid4().hex[:4]}"
        markup_str = f'<tag {tag_key}="{tag_val}" />'
        parsed_attrs = self.extractor.parse_attributes(markup_str)
        self.assertEqual(parsed_attrs.get(tag_key), tag_val)

        extracted_data = self.extractor.extract(markup_str)
        self.assertTrue(extracted_data.get("parsed"))

        pipeline_input = {
            "anomaly_id": self.unique_id,
            "metric": metric_val,
            "attributes": parsed_attrs
        }
        pipeline_output = start_pipeline(pipeline_input)
        self.assertTrue(pipeline_output.get("filtered"))
        self.assertEqual(pipeline_output.get("anomaly_id"), self.unique_id)

        commits = self.inspector.get_commit_history(max_count=5)
        self.assertIsInstance(commits, list)
        self.assertGreater(len(commits), 0)
        commit_hash = commits[0].get("commit")

        file_content = self.inspector.read_file_at_commit(commit_hash, "dummy_path.py")
        self.assertIsInstance(file_content, bytes)

        repo_status = self.inspector.analyze_repository()
        self.assertIsInstance(repo_status, dict)

        final_report = self.hub.generate_final_report()
        self.assertIn("report_", final_report.get("report_id"))
        
        reported_metrics = final_report.get("metrics")
        self.assertEqual(len(reported_metrics), 1)
        self.assertEqual(reported_metrics[0]["name"], metric_name)
        self.assertEqual(reported_metrics[0]["value"], metric_val)

        reported_anomalies = final_report.get("anomalies")
        self.assertEqual(len(reported_anomalies), 1)
        logged_anomaly = reported_anomalies[0]
        
        self.assertEqual(logged_anomaly["source"], source_name)
        self.assertEqual(logged_anomaly["severity"], severity_level)
        self.assertEqual(logged_anomaly["details"], details_msg)
        self.assertEqual(logged_anomaly["telemetry"], telemetry_data)

        structured_report = self.logger.get_structured_report()
        self.assertIn("anomalies", structured_report)
        self.assertEqual(len(structured_report["anomalies"]), 1)

        self.assertTrue(os.path.exists(self.log_path))

if __name__ == "__main__":
    unittest.main()