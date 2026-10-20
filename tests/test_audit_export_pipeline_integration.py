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
        self.output_json = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")
        self.output_html = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.html")

        self.threshold = round(random.uniform(0.5, 0.9), 2)

        self.pipeline = AuditExportPipeline(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pipeline_composition_and_execution(self):
        self.assertIsInstance(self.pipeline.audit_hub, AnomalyAuditHub)

        source_name = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_text = f"Anomalous telemetry detected: {uuid.uuid4()}"
        telemetry_data = {
            "cpu_load": round(random.uniform(80.0, 99.9), 2),
            "memory_leak_mb": random.randint(500, 2048)
        }

        self.pipeline.audit_hub.log_anomaly(
            source=source_name,
            severity=severity_level,
            details=details_text,
            telemetry_snapshot=telemetry_data
        )

        metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        metric_val = round(random.uniform(10.0, 100.0), 2)
        self.pipeline.audit_hub.aggregate_and_report(metric_name=metric_key, value=metric_val)

        json_result_path = self.pipeline.export_pipeline_report(self.output_json)
        self.assertEqual(json_result_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json))

        with open(self.output_json, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(source_name, content)
            self.assertIn(str(metric_val), content)

        html_result_path = self.pipeline.export_pipeline_html(self.output_html)
        self.assertEqual(html_result_path, self.output_html)
        self.assertTrue(os.path.exists(self.output_html))

        with open(self.output_html, "r", encoding="utf-8") as f:
            html_content = f.read()
            self.assertGreater(len(html_content), 0)


if __name__ == "__main__":
    unittest.main()