import unittest
import os
import tempfile
import uuid
import random

from skills.digest_audit_pipeline import DigestAuditPipeline
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class TestDigestAuditPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.log_path = os.path.join(self.repo_path, f"audit_{uuid.uuid4()}.log")
        self.output_json = os.path.join(self.repo_path, f"report_{uuid.uuid4()}.json")
        self.output_html = os.path.join(self.repo_path, f"report_{uuid.uuid4()}.html")

        self.threshold = round(random.uniform(0.5, 0.9), 2)
        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        self.metric_value = round(random.uniform(10.0, 100.0), 2)

        self.source = f"source_{uuid.uuid4().hex[:6]}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.details = f"Anomalous behavior detected: {uuid.uuid4()}"
        self.telemetry = {"cpu_load": random.randint(50, 100), "memory": random.randint(1024, 8192)}

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_real_integration_and_export(self):
        pipeline = DigestAuditPipeline(
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
            telemetry_snapshot=self.telemetry
        )

        pipeline.audit_hub.aggregate_and_report(
            metric_name=self.metric_name,
            value=self.metric_value
        )

        json_result_path = pipeline.export_comprehensive_json(self.output_json)
        html_result_path = pipeline.export_comprehensive_html(self.output_html)

        self.assertEqual(json_result_path, self.output_json)
        self.assertTrue(os.path.exists(self.output_json), "JSON отчёт должен быть физически создан на диске.")

        with open(self.output_json, "r", encoding="utf-8") as f:
            content_json = f.read()
            self.assertIn(self.source, content_json)
            self.assertIn(self.details, content_json)
            self.assertIn(self.metric_name, content_json)

        self.assertEqual(html_result_path, self.output_html)
        self.assertTrue(os.path.exists(self.output_html), "HTML отчёт должен быть физически создан на диске.")

        with open(self.output_html, "r", encoding="utf-8") as f:
            content_html = f.read()
            self.assertGreater(len(content_html), 0, "HTML отчет не должен быть пустым.")


if __name__ == "__main__":
    unittest.main()