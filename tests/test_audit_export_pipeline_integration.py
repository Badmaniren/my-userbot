import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.audit_export_pipeline import AuditExportPipeline


class TestAuditExportPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.log_path = os.path.join(self.test_dir, f"audit_{uuid.uuid4()}.log")
        self.output_path = os.path.join(self.test_dir, f"report_{uuid.uuid4()}.json")
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.pipeline = AuditExportPipeline(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pipeline_integration_end_to_end(self):
        source_name = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_text = f"Test anomaly detail {uuid.uuid4()}"
        telemetry_data = {"cpu_load": random.randint(10, 100), "memory_usage": random.randint(500, 4000)}

        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = round(random.uniform(1.0, 100.0), 2)

        self.pipeline.audit_hub.log_anomaly(
            source=source_name,
            severity=severity_level,
            details=details_text,
            telemetry_snapshot=telemetry_data
        )

        report_result = self.pipeline.audit_hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        self.assertIsNotNone(report_result)

        exported_file = self.pipeline.export_pipeline_report(self.output_path)

        self.assertTrue(os.path.exists(exported_file), "Экспортированный файл отчета должен реально существовать на диске")

        with open(exported_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(source_name, content, "Отчет должен содержать информацию о залогированной аномалии")
            self.assertIn(metric_name, content, "Отчет должен содержать агрегированную метрику")


if __name__ == "__main__":
    unittest.main()