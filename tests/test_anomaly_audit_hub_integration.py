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
        self.log_file = os.path.join(self.test_dir, f"anomaly_{uuid.uuid4()}.log")
        self.repo_path = self.test_dir
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_end_to_end_anomaly_audit_flow(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        metric_val = round(random.uniform(0.0, 100.0), 2)

        details_payload = {
            "error_code": random.randint(500, 599),
            "message": f"Random failure event {uuid.uuid4()}"
        }
        telemetry_snapshot_data = {
            "cpu_usage": round(random.uniform(10.0, 99.9), 2),
            "memory_free": random.randint(1024, 8192)
        }

        log_result = self.audit_hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details_payload,
            telemetry_snapshot=telemetry_snapshot_data
        )

        self.assertTrue(
            os.path.exists(self.log_file),
            "Интеграционный сбой: лог-файл не был создан при вызове log_anomaly через AnomalyAuditHub."
        )

        aggregation_result = self.audit_hub.aggregate_and_report(
            metric_name=metric_key,
            value=metric_val
        )

        final_report = self.audit_hub.generate_final_report()

        self.assertIsNotNone(
            final_report,
            "Интеграционный сбой: generate_final_report вернул None."
        )

        self.assertIn(
            metric_key,
            str(final_report),
            f"Интеграционный сбой: метрика '{metric_key}' отсутствует в итоговом отчете безопасности."
        )

if __name__ == "__main__":
    unittest.main()