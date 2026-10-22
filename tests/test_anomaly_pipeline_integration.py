import unittest
import tempfile
import shutil
import uuid
import random
import os
from skills.anomaly_pipeline import AnomalyPipeline
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.test_dir, f"audit_{uuid.uuid4()}.log")
        self.repo_path = os.path.join(self.test_dir, f"repo_{uuid.uuid4()}")
        os.makedirs(self.repo_path, exist_ok=True)

        self.threshold = round(random.uniform(0.5, 9.9), 2)
        self.pipeline = AnomalyPipeline(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pipeline_composition_and_logging_integration(self):
        self.assertIsInstance(self.pipeline.audit_hub, AnomalyAuditHub)
        self.assertIsInstance(self.pipeline.logger, AnomalyLogger)

        source_id = f"service_{uuid.uuid4()}"
        severity_val = random.randint(1, 10)
        detail_msg = f"random_anomaly_event_{uuid.uuid4()}"
        telemetry_data = {
            "cpu_load": round(random.uniform(10.0, 99.9), 2),
            "memory_usage": uuid.uuid4().hex
        }

        self.pipeline.process_and_log_anomaly(
            source=source_id,
            severity=severity_val,
            details=detail_msg,
            telemetry_snapshot=telemetry_data
        )

        anomalies_from_logger = self.pipeline.logger.get_anomalies()
        self.assertTrue(any(detail_msg in str(a) for a in anomalies_from_logger), "Аномалия не найдена в логгере пайплайна")

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(100.0, 500.0), 2)

        report_data = self.pipeline.audit_hub.aggregate_and_report(metric_name, metric_value)
        self.assertIsNotNone(report_data)

        final_report = self.pipeline.audit_hub.generate_final_report()
        self.assertIsNotNone(final_report)

        self.assertTrue(os.path.exists(self.log_path), "Файл лога аудита не был создан на диске")

if __name__ == '__main__':
    unittest.main()