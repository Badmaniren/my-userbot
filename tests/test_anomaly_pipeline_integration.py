import unittest
import os
import json
import uuid
import random
from skills.anomaly_pipeline import AnomalyAuditHub, AnomalyLogger, start_pipeline, ExtractorTool, GitInspector

class TestAnomalyPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.log_path = os.path.join("test_logs", f"anomaly_{self.unique_suffix}.log")
        self.repo_path = f"/tmp/repo_{self.unique_suffix}"
        self.threshold = random.uniform(0.1, 0.9)
        
        self.audit_hub = AnomalyAuditHub(self.repo_path, self.log_path, self.threshold)

    def tearDown(self):
        if os.path.exists(self.log_path):
            try:
                os.remove(self.log_path)
                log_dir = os.path.dirname(self.log_path)
                if os.path.exists(log_dir) and not os.listdir(log_dir):
                    os.rmdir(log_dir)
            except OSError:
                pass

    def test_integration_pipeline_and_audit_flow(self):
        source_name = f"source_{uuid.uuid4().hex[:6]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_msg = f"Detailed error description {uuid.uuid4()}"
        telemetry_data = {
            "cpu_usage": random.randint(10, 100),
            "memory_mb": random.randint(512, 8192),
            "random_marker": uuid.uuid4().hex
        }

        self.audit_hub.log_anomaly(source_name, severity_level, details_msg, telemetry_data)

        metric_key = f"metric_{uuid.uuid4().hex[:4]}"
        metric_val = random.uniform(1.0, 100.0)
        aggregation_result = self.audit_hub.aggregate_and_report(metric_key, metric_val)
        self.assertTrue(aggregation_result)

        final_report = self.audit_hub.generate_final_report()
        
        self.assertIn("report_id", final_report)
        self.assertTrue(final_report["report_id"].endswith(os.path.basename(self.log_path)))
        
        self.assertEqual(len(final_report["metrics"]), 1)
        self.assertEqual(final_report["metrics"][0]["name"], metric_key)
        self.assertEqual(final_report["metrics"][0]["value"], metric_val)

        self.assertEqual(len(final_report["anomalies"]), 1)
        logged_anomaly = final_report["anomalies"][0]
        self.assertEqual(logged_anomaly["source"], source_name)
        self.assertEqual(logged_anomaly["severity"], severity_level)
        self.assertEqual(logged_anomaly["details"], details_msg)
        self.assertEqual(logged_anomaly["telemetry"]["random_marker"], telemetry_data["random_marker"])

        self.assertTrue(os.path.exists(self.log_path), "Log file must be created on disk.")

        pipeline_input = {
            "pipeline_id": uuid.uuid4().hex,
            "val": random.randint(1, 500)
        }
        pipeline_output = start_pipeline(pipeline_input)
        self.assertTrue(pipeline_output.get("filtered"))
        self.assertEqual(pipeline_output["pipeline_id"], pipeline_input["pipeline_id"])
        self.assertEqual(pipeline_output["val"], pipeline_input["val"])

        extractor = ExtractorTool()
        attr_key = f"attr_{uuid.uuid4().hex[:4]}"
        attr_val = uuid.uuid4().hex
        tag_str = f'{attr_key}="{attr_val}"'
        parsed_attrs = extractor.parse_attributes(tag_str)
        self.assertEqual(parsed_attrs.get(attr_key), attr_val)

        markup_sample = f"<div>{uuid.uuid4().hex}</div>"
        extraction_res = extractor.extract(markup_sample)
        self.assertTrue(extraction_res.get("parsed"))
        self.assertEqual(extraction_res["markup"], markup_sample)

        inspector = GitInspector(self.repo_path)
        commits = inspector.get_commit_history()
        self.assertIsInstance(commits, list)
        self.assertGreater(len(commits), 0)
        self.assertIn("commit", commits[0])

        file_content = inspector.read_file_at_commit(commits[0]["commit"], f"file_{uuid.uuid4().hex}.py")
        self.assertIsInstance(file_content, bytes)

        repo_analysis = inspector.analyze_repository()
        self.assertIsInstance(repo_analysis, dict)
        self.assertIn("status", repo_analysis)

if __name__ == "__main__":
    unittest.main()