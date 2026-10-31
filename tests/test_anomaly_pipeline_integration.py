import unittest
import os
import uuid
import random
from skills.anomaly_pipeline import (
    AnomalyLogger,
    AnomalyAuditHub,
    start_pipeline,
    ExtractorTool,
    GitInspector
)

class TestAnomalyPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = uuid.uuid4().hex
        self.log_path = f"test_logs_{self.unique_id}/anomaly.log"
        self.repo_path = f"/tmp/repo_{self.unique_id}"
        self.threshold = random.uniform(0.1, 0.9)

    def tearDown(self):
        if os.path.exists(self.log_path):
            try:
                os.remove(self.log_path)
                os.rmdir(os.path.dirname(self.log_path))
            except OSError:
                pass

    def test_pipeline_and_audit_hub_integration(self):
        source = f"service_{uuid.uuid4().hex[:6]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {"error_code": random.randint(500, 599), "message": uuid.uuid4().hex}
        telemetry_snapshot = {"cpu_usage": random.uniform(10.0, 99.9), "memory_mb": random.randint(1024, 8192)}

        audit_hub = AnomalyAuditHub(self.repo_path, self.log_path, self.threshold)
        
        audit_hub.log_anomaly(source, severity, details, telemetry_snapshot)
        
        metric_name = f"metric_{uuid.uuid4().hex[:4]}"
        metric_value = random.randint(1, 100)
        aggregation_result = audit_hub.aggregate_and_report(metric_name, metric_value)
        self.assertTrue(aggregation_result)

        final_report = audit_hub.generate_final_report()
        self.assertIn("report_id", final_report)
        self.assertTrue(final_report["report_id"].endswith(os.path.basename(self.log_path)))
        self.assertEqual(len(final_report["metrics"]), 1)
        self.assertEqual(final_report["metrics"][0]["name"], metric_name)
        self.assertEqual(final_report["metrics"][0]["value"], metric_value)

        anomalies = final_report["anomalies"]
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["source"], source)
        self.assertEqual(anomalies[0]["severity"], severity)
        self.assertEqual(anomalies[0]["details"], details)
        self.assertEqual(anomalies[0]["telemetry"], telemetry_snapshot)

        logger = AnomalyLogger(self.log_path)
        structured_report = logger.get_structured_report()
        self.assertIn("anomalies", structured_report)
        self.assertEqual(len(structured_report["anomalies"]), 1)

        input_payload = {str(uuid.uuid4()): random.randint(1, 1000)}
        pipeline_res = start_pipeline(input_payload)
        self.assertTrue(pipeline_res.get("filtered"))
        for k, v in input_payload.items():
            self.assertEqual(pipeline_res.get(k), v)

        extractor = ExtractorTool()
        tag_name = f"tag_{uuid.uuid4().hex[:4]}"
        attr_key = f"key_{uuid.uuid4().hex[:4]}"
        attr_val = uuid.uuid4().hex[:8]
        tag_string = f'<{tag_name} {attr_key}="{attr_val}"></{tag_name}>'
        
        parsed_attrs = extractor.parse_attributes(tag_string)
        self.assertEqual(parsed_attrs.get(attr_key), attr_val)

        extracted_data = extractor.extract(tag_string)
        self.assertTrue(extracted_data.get("parsed"))
        self.assertEqual(extracted_data.get("markup"), tag_string)

        inspector = GitInspector(self.repo_path)
        commits = inspector.get_commit_history(max_count=5)
        self.assertIsInstance(commits, list)
        self.assertTrue(len(commits) > 0)
        commit_hash = commits[0].get("commit")
        
        file_content = inspector.read_file_at_commit(commit_hash, "some_path.py")
        self.assertIsInstance(file_content, bytes)

        repo_analysis = inspector.analyze_repository()
        self.assertIsInstance(repo_analysis, dict)
        self.assertIn("status", repo_analysis)

if __name__ == "__main__":
    unittest.main()