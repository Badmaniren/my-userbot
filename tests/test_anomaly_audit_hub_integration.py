import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.log_file = os.path.join(self.repo_path, f"audit_log_{uuid.uuid4().hex}.json")
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_anomaly_audit_hub_end_to_end_workflow(self):
        source = f"service_{uuid.uuid4().hex[:6]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(0.0, 100.0), 2)

        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Random failure token {uuid.uuid4()}"
        }
        telemetry_snapshot = {
            "cpu_usage": round(random.uniform(10.0, 99.9), 1),
            "memory_usage": round(random.uniform(20.0, 95.0), 1)
        }

        log_result = self.audit_hub.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertTrue(
            os.path.exists(self.log_file),
            "Интеграционный сбой: лог-файл не был создан реальным модулем AnomalyLogger."
        )

        aggregation_result = self.audit_hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        self.assertIsNotNone(
            aggregation_result,
            "Интеграционный сбой: агрегатор не вернул результат."
        )

        final_report = self.audit_hub.generate_final_report()

        self.assertIsNotNone(
            final_report,
            "Интеграционный сбой: итоговый отчёт не сгенерирован."
        )

        with open(self.log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
            self.assertIn(
                source,
                log_content,
                "Интеграционный сбой: источник аномалии отсутствует в физическом файле логов."
            )
            self.assertIn(
                str(details["error_code"]),
                log_content,
                "Интеграционный сбой: детали аномалии не записаны в лог-файл."
            )


if __name__ == "__main__":
    unittest.main()