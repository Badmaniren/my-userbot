import unittest
import os
import tempfile
import uuid
import random
from skills.audit_export_pipeline import AuditExportPipeline
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class TestAuditExportPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.log_path = os.path.join(self.repo_path, f"audit_{uuid.uuid4()}.log")
        self.output_json_path = os.path.join(self.repo_path, f"report_{uuid.uuid4()}.json")
        self.output_html_path = os.path.join(self.repo_path, f"report_{uuid.uuid4()}.html")

        self.threshold = round(random.uniform(0.1, 0.9), 2)
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.metric_value = round(random.uniform(10.0, 100.0), 2)

        self.source = f"source_{uuid.uuid4().hex[:6]}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.details = f"Anomaly details {uuid.uuid4()}"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_real_integration(self):
        pipeline = AuditExportPipeline(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        self.assertIsInstance(pipeline.audit_hub, AnomalyAuditHub)
        self.assertIsInstance(pipeline.exporter, DigestExporter)

        pipeline.audit_hub.log_anomaly(
            source=self.source,
            severity=self.severity,
            details=self.details,
            telemetry_snapshot={"cpu": random.randint(10, 99)}
        )

        pipeline.audit_hub.aggregate_and_report(
            metric_name=self.metric_name,
            value=self.metric_value
        )

        json_result_path = pipeline.export_pipeline_report(self.output_json_path, format_type="json")

        self.assertTrue(os.path.exists(json_result_path))
        self.assertEqual(os.path.abspath(json_result_path), os.path.abspath(self.output_json_path))

        with open(json_result_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertGreater(len(content), 0)

        html_result_path = pipeline.export_pipeline_report(self.output_html_path, format_type="html")

        self.assertTrue(os.path.exists(html_result_path))
        self.assertEqual(os.path.abspath(html_result_path), os.path.abspath(self.output_html_path))

        with open(html_result_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            self.assertIn("<html", html_content.lower())


if __name__ == "__main__":
    unittest.main()
