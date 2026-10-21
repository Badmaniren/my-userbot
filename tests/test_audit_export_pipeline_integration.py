import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.audit_export_pipeline import AuditExportPipeline
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class TestAuditExportPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.log_path = os.path.join(self.test_dir, "audit.log")
        self.output_json = os.path.join(self.test_dir, f"report_{uuid.uuid4()}.json")
        self.output_html = os.path.join(self.test_dir, f"report_{uuid.uuid4()}.html")

        self.source = f"service_{uuid.uuid4().hex[:6]}"
        self.severity = random.choice(["INFO", "WARNING", "CRITICAL"])
        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        self.metric_value = round(random.uniform(10.0, 100.0), 2)
        self.details = f"Integration test run id: {uuid.uuid4()}"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pipeline_composition_and_export(self):
        pipeline = AuditExportPipeline(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=random.randint(5, 15)
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

        pipeline.audit_hub.generate_final_report()

        json_result = pipeline.export_report(self.output_json, format="json")
        self.assertTrue(os.path.exists(json_result))
        self.assertGreater(os.path.getsize(json_result), 0)

        html_result = pipeline.export_report(self.output_html, format="html")
        self.assertTrue(os.path.exists(html_result))
        self.assertGreater(os.path.getsize(html_result), 0)


if __name__ == "__main__":
    unittest.main()