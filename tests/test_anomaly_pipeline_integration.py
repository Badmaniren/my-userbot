import unittest
import os
import json
import uuid
import random
from skills.anomaly_pipeline import AnomalyLogger, AnomalyAuditHub, start_pipeline, ExtractorTool, GitInspector

class TestAnomalyPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.log_path = f"test_anomaly_{self.random_suffix}.log"
        self.repo_path = f"/tmp/repo_{self.random_suffix}"
        
        self.logger = AnomalyLogger(log_path=self.log_path)
        self.logger.clear_logs()

    def tearDown(self):
        if os.path.exists(self.log_path):
            try:
                os.remove(self.log_path)
            except OSError:
                pass

    def test_full_pipeline_and_audit_integration(self):
        source_name = f"source_{uuid.uuid4().hex[:6]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_msg = f"Test anomaly details {uuid.uuid4()}"
        telemetry_data = {"cpu_load": random.random(), "memory_usage": random.randint(100, 500)}

        hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_path, threshold=0.5)
        
        hub.log_anomaly(source_name, severity_level, details_msg, telemetry_data)
        
        metric_name = f"metric_{uuid.uuid4().hex[:4]}"
        metric_val = random.uniform(0.0, 1.0)
        agg_result = hub.aggregate_and_report(metric_name, metric_val)
        self.assertTrue(agg_result)

        is_correlated = hub.correlate_metric(metric_val)
        self.assertIsInstance(is_correlated, bool)

        report = hub.generate_final_report()
        self.assertIn("report_id", report)
        self.assertIn(os.path.basename(self.log_path), report["report_id"])
        self.assertEqual(len(report["metrics"]), 1)
        self.assertEqual(report["metrics"][0]["name"], metric_name)
        self.assertEqual(report["metrics"][0]["value"], metric_val)

        anomalies = report["anomalies"]
        self.assertEqual(len(anomalies), 1)
        logged_anomaly = anomalies[0]
        self.assertEqual(logged_anomaly["source"], source_name)
        self.assertEqual(logged_anomaly["severity"], severity_level)
        self.assertEqual(logged_anomaly["details"], details_msg)
        self.assertEqual(logged_anomaly["telemetry"], telemetry_data)

        pipeline_input = {"random_key": uuid.uuid4().hex, "val": random.randint(1, 100)}
        pipeline_output = start_pipeline(pipeline_input)
        self.assertTrue(pipeline_output.get("filtered"))
        self.assertEqual(pipeline_output["random_key"], pipeline_input["random_key"])

        extractor = ExtractorTool()
        tag_str = f'id="tag_{uuid.uuid4().hex[:4]}" class="active"'
        parsed_attrs = extractor.parse_attributes(tag_str)
        self.assertIn("id", parsed_attrs)
        self.assertIn("class", parsed_attrs)

        markup_data = f"<div>{uuid.uuid4()}</div>"
        extracted_res = extractor.extract(markup_data)
        self.assertTrue(extracted_res["parsed"])
        self.assertEqual(extracted_res["markup"], markup_data)

        inspector = GitInspector(self.repo_path)
        commits = inspector.get_commit_history(max_count=5)
        self.assertIsInstance(commits, list)
        self.assertTrue(len(commits) > 0)

        file_content = inspector.read_file_at_commit(commits[0]["commit"], "any_file.py")
        self.assertIsInstance(file_content, bytes)

        repo_analysis = inspector.analyze_repository()
        self.assertIsInstance(repo_analysis, dict)
        self.assertIn("status", repo_analysis)

        structured = self.logger.get_structured_report()
        self.assertIn("anomalies", structured)
        self.assertEqual(len(structured["anomalies"]), 1)

if __name__ == "__main__":
    unittest.main()