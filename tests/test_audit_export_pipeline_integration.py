import unittest
import tempfile
import os
import uuid
import random
from skills.audit_export_pipeline import AuditExportPipeline

class TestAuditExportPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.log_path = os.path.join(self.repo_path, f"audit_{uuid.uuid4().hex}.log")
        self.export_output_path = os.path.join(self.repo_path, f"export_report_{uuid.uuid4().hex}.json")

        self.threshold = random.uniform(0.5, 5.0)
        self.pipeline = AuditExportPipeline(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pipeline_integration_flow(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["INFO", "WARNING", "CRITICAL"])
        details_msg = f"Random test anomaly detail: {uuid.uuid4()}"

        telemetry_data = {
            "cpu_load": random.uniform(10.0, 99.9),
            "memory_usage": random.randint(1024, 8192)
        }

        self.pipeline.hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details_msg,
            telemetry_snapshot=telemetry_data
        )

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_val = random.uniform(100.0, 1000.0)
        self.pipeline.hub.aggregate_and_report(metric_name, metric_val)

        exported_file = self.pipeline.run_export(self.export_output_path)

        self.assertTrue(os.path.exists(exported_file), "Экспортированный файл отчета должен реально существовать на диске")

        file_size = os.path.getsize(exported_file)
        self.assertGreater(file_size, 0, "Экспортированный файл отчета не должен быть пустым")

        with open(exported_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(source_id, content, "Отчет должен содержать источник аномалии, переданный в пайплайн")
            self.assertIn(details_msg, content, "Отчет должен содержать детали аномалии")

if __name__ == '__main__':
    unittest.main()