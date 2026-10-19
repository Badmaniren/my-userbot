import unittest
import os
import tempfile
import shutil
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.log_file = os.path.join(self.test_dir, f"audit_{uuid.uuid4().hex}.json")
        self.threshold = round(random.uniform(0.1, 0.9), 2)
        
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_audit_hub_integration_lifecycle(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severity_levels)

        random_error_code = random.randint(1000, 9999)
        details = {
            "error_code": random_error_code,
            "message": f"Integration test anomaly {uuid.uuid4().hex}"
        }

        telemetry_snapshot = {
            "cpu_load": round(random.uniform(10.0, 99.9), 2),
            "memory_usage": round(random.uniform(20.0, 95.0), 2)
        }

        log_result = self.audit_hub.log_anomaly(
            source=source_id,
            severity=chosen_severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        
        self.assertIsNotNone(log_result, "Метод log_anomaly не должен возвращать None")

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(0.0, 100.0), 2)

        aggregate_result = self.audit_hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        
        self.assertIsNotNone(aggregate_result, "Метод aggregate_and_report не должен возвращать None")

        final_report = self.audit_hub.generate_final_report()
        self.assertIsNotNone(final_report, "Финальный отчет не должен быть пустым")

        self.assertTrue(os.path.exists(self.log_file), "Лог-файл должен быть создан в процессе работы аудита")

if __name__ == "__main__":
    unittest.main()