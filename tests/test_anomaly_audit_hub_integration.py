import unittest
import tempfile
import os
import shutil
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, f"audit_log_{uuid.uuid4().hex}.json")
        self.repo_path = self.test_dir
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_audit_lifecycle_integration(self):
        source_name = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(1.0, 100.0), 2)

        details_data = {
            "error_code": random.randint(1000, 9999),
            "description": f"Random failure token {uuid.uuid4().hex}"
        }
        telemetry_snapshot = {
            "cpu_usage": round(random.uniform(10.0, 99.9), 1),
            "memory_free": random.randint(1024, 8192)
        }

        log_result = self.audit_hub.log_anomaly(
            source=source_name,
            severity=severity_level,
            details=details_data,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertIsNotNone(log_result, "Метод log_anomaly не должен возвращать None")

        agg_result = self.audit_hub.aggregate_and_report(
            metric_name=metric_key,
            value=metric_value
        )

        self.assertIsNotNone(agg_result, "Метод aggregate_and_report не должен возвращать None")

        final_report = self.audit_hub.generate_final_report()

        self.assertIsNotNone(final_report, "Финальный отчет безопасности не должен быть пустым")

        report_str = str(final_report)
        self.assertIn(metric_key, report_str, "Финальный отчет должен содержать агрегированную метрику")
        self.assertTrue(os.path.exists(self.log_file), "Файл логов должен быть физически создан в процессе работы")

if __name__ == "__main__":
    unittest.main()