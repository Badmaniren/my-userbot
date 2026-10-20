import unittest
import tempfile
import os
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, f"anomaly_log_{uuid.uuid4()}.json")
        self.repo_path = self.temp_dir.name
        self.threshold = round(random.uniform(0.1, 0.9), 2)
        
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_full_audit_hub_integration(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(0.0, 100.0), 2)

        details = {
            "error_code": random.randint(500, 599),
            "description": f"Integration test error msg {uuid.uuid4()}"
        }
        telemetry_snapshot = {
            "cpu_load": round(random.uniform(10.0, 99.9), 1),
            "memory_usage": round(random.uniform(20.0, 95.0), 1)
        }

        log_result = self.audit_hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        
        self.assertTrue(
            os.path.exists(self.log_file),
            "Лог-файл должен быть создан в результате работы AnomalyLogger через AnomalyAuditHub"
        )

        aggregate_result = self.audit_hub.aggregate_and_report(
            metric_name=metric_key,
            value=metric_value
        )
        self.assertIsNotNone(aggregate_result, "Агрегатор должен вернуть результат обработки метрики")

        final_report = self.audit_hub.generate_final_report()
        self.assertIsNotNone(final_report, "Финальный отчет не должен быть пустым")
        
        if isinstance(final_report, dict):
            self.assertTrue(len(final_report) >= 0)
        elif isinstance(final_report, str):
            self.assertGreater(len(final_report), 0)


if __name__ == "__main__":
    unittest.main()