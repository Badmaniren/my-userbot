import unittest
import os
import tempfile
import shutil
import uuid
import random

from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter
from skills.audit_exporter_pipeline import AuditExporterPipeline

class TestAuditExporterPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.log_path = os.path.join(self.test_dir, "audit_log.json")
        self.output_json = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")

        self.threshold = random.uniform(0.5, 0.9)
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        self.digest_exporter = DigestExporter(
            stability_digest=None,
            anomaly_visualizer=None
        )

        self.pipeline = AuditExporterPipeline(
            audit_hub=self.audit_hub,
            exporter=self.digest_exporter
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pipeline_integration_flow(self):
        source_name = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        metric_val = random.randint(100, 1000)

        details_data = {
            "error_code": random.randint(500, 599),
            "message": f"Integration test error {uuid.uuid4().hex}"
        }
        telemetry_data = {
            "cpu_load": random.uniform(10.0, 99.0),
            "memory_usage": random.uniform(20.0, 95.0)
        }

        self.audit_hub.log_anomaly(
            source=source_name,
            severity=severity_level,
            details=details_data,
            telemetry_snapshot=telemetry_data
        )

        self.audit_hub.aggregate_and_report(
            metric_name=metric_key,
            value=metric_val
        )

        pipeline_result = self.pipeline.run_pipeline(output_path=self.output_json)

        self.assertTrue(os.path.exists(self.output_json), "Экспортированный файл отчета должен быть создан на диске.")

        with open(self.output_json, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(source_name, content, "Отчет должен содержать источник аномалии.")
            self.assertIn(metric_key, content, "Отчет должен содержать метку агрегации.")

        self.assertIsNotNone(pipeline_result, "Конвейер должен возвращать результат выполнения.")

if __name__ == '__main__':
    unittest.main()