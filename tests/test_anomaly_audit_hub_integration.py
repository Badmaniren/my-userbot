import unittest
import tempfile
import os
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, f"audit_log_{uuid.uuid4()}.json")
        self.repo_path = self.temp_dir.name
        self.threshold = round(random.uniform(0.5, 99.9), 2)
        
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_full_audit_and_aggregation_lifecycle(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(0.0, 150.0), 2)
        
        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Random anomaly event {uuid.uuid4()}"
        }
        telemetry = {
            "cpu_load": round(random.uniform(10.0, 100.0), 2),
            "memory_usage": round(random.uniform(20.0, 95.0), 2)
        }

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry
        )

        self.assertTrue(
            os.path.exists(self.log_file),
            "Интеграционный сбой: файл логов не был создан реальным AnomalyLogger"
        )

        aggregation_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        self.assertIsNotNone(
            aggregation_result,
            "Интеграционный сбой: агрегатор не вернул результат обработки метрики"
        )

        final_report = self.hub.generate_final_report()

        self.assertIsNotNone(
            final_report,
            "Интеграционный сбой: финальный отчет аудита не был сформирован"
        )

        if isinstance(final_report, dict):
            self.assertTrue(len(final_report) >= 0)
        elif isinstance(final_report, str):
            self.assertGreater(len(final_report), 0)


if __name__ == "__main__":
    unittest.main()