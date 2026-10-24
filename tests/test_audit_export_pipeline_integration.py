import unittest
import os
import tempfile
import uuid
import random
from skills.audit_export_pipeline import AuditExportPipeline

class TestAuditExportPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.log_path = os.path.join(self.repo_path, f"audit_{uuid.uuid4().hex}.log")
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.pipeline = AuditExportPipeline(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pipeline_full_workflow_json(self):
        source_id = f"source_{uuid.uuid4().hex[:8]}"
        severity_levels = ["INFO", "WARNING", "CRITICAL", "ERROR"]
        severity = random.choice(severity_levels)
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(10.0, 100.0), 2)

        details = {"error_code": random.randint(1000, 9999), "message": "integration test anomaly"}
        telemetry = {"cpu_load": random.random(), "memory_usage": random.randint(200, 800)}

        self.pipeline.log_pipeline_anomaly(
            source=source_id,
            severity=severity,
            details=details,
            telemetry=telemetry
        )

        self.pipeline.aggregate_metric(metric_name, metric_value)

        output_json = os.path.join(self.repo_path, f"report_{uuid.uuid4().hex}.json")
        result_path = self.pipeline.export_report(output_json, format="json")

        self.assertTrue(os.path.exists(result_path))
        self.assertEqual(os.path.abspath(result_path), os.path.abspath(output_json))

        with open(result_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertGreater(len(content), 0)

    def test_pipeline_full_workflow_html(self):
        source_id = f"source_{uuid.uuid4().hex[:8]}"
        severity = random.choice(["LOW", "HIGH"])
        metric_name = f"latency_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(0.5, 50.0), 2)

        self.pipeline.log_pipeline_anomaly(
            source=source_id,
            severity=severity,
            details={"action": "test_html_export"},
            telemetry={"uptime": random.randint(10000, 50000)}
        )

        self.pipeline.aggregate_metric(metric_name, metric_value)

        output_html = os.path.join(self.repo_path, f"report_{uuid.uuid4().hex}.html")
        result_path = self.pipeline.run_audit_and_export_html(output_html)

        self.assertTrue(os.path.exists(result_path))
        self.assertEqual(os.path.abspath(result_path), os.path.abspath(output_html))

        with open(result_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertGreater(len(content), 0)

if __name__ == "__main__":
    unittest.main()