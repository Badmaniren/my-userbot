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
        self.output_json_path = os.path.join(self.test_dir, f"report_{uuid.uuid4()}.json")
        self.output_html_path = os.path.join(self.test_dir, f"report_{uuid.uuid4()}.html")

        self.threshold = round(random.uniform(0.5, 0.9), 2)

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        self.pipeline = AuditExportPipeline(
            audit_hub=self.audit_hub
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pipeline_integration_flow(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_msg = f"Test anomaly event {uuid.uuid4()}"
        telemetry_data = {
            "cpu_load": round(random.uniform(10.0, 99.9), 2),
            "memory_usage": round(random.uniform(20.0, 95.0), 2)
        }

        self.audit_hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details_msg,
            telemetry_snapshot=telemetry_data
        )

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(1.0, 100.0), 2)
        self.audit_hub.aggregate_and_report(metric_name=metric_name, value=metric_value)

        json_result = self.pipeline.export_json(self.output_json_path)

        self.assertTrue(os.path.exists(self.output_json_path), "JSON export file must be created on disk")
        self.assertGreater(os.path.getsize(self.output_json_path), 0, "JSON export file must not be empty")
        with open(self.output_json_path, 'r', encoding='utf-8') as f:
            json_content = f.read()
        self.assertIn(source_id, json_content, "Exported data must contain the logged anomaly source")

        html_result = self.pipeline.export_html(self.output_html_path)

        self.assertTrue(os.path.exists(self.output_html_path), "HTML export file must be created on disk")
        self.assertGreater(os.path.getsize(self.output_html_path), 0, "HTML export file must not be empty")


if __name__ == "__main__":
    unittest.main()