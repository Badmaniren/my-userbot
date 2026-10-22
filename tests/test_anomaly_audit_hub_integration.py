import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, f"audit_{uuid.uuid4()}.log")
        self.repo_path = self.test_dir
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_anomaly_audit_hub_integration_workflow(self):
        source_id = f"source-{uuid.uuid4()}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(0.0, 100.0), 2)

        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Random failure description {uuid.uuid4()}"
        }
        telemetry_snapshot = {
            "cpu_usage": round(random.uniform(10.0, 99.9), 1),
            "memory_free": random.randint(1024, 8192)
        }

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertTrue(
            os.path.exists(self.log_file),
            "Интеграционный сбой: Лог-файл не был создан реальным AnomalyLogger."
        )

        agg_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        self.assertIsNotNone(agg_result, "Агрегация не должна возвращать None.")

        final_report = self.hub.generate_final_report()
        self.assertIsNotNone(final_report, "Финальный отчет должен быть сформирован.")

        report_str = str(final_report)
        self.assertIn(metric_name, report_str, "Имя метрики должно присутствовать в итоговом отчете.")

if __name__ == "__main__":
    unittest.main()