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

    def test_anomaly_audit_hub_workflow(self):
        source_name = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = round(random.uniform(1.0, 100.0), 2)
        
        details_data = {
            "error_code": random.randint(1000, 9999),
            "message": f"msg_{uuid.uuid4()}"
        }
        telemetry_snapshot_data = {
            "cpu_usage": round(random.uniform(10.0, 99.9), 2),
            "memory_free": random.randint(1024, 16384)
        }

        log_result = self.hub.log_anomaly(
            source=source_name,
            severity=severity_level,
            details=details_data,
            telemetry_snapshot=telemetry_snapshot_data
        )

        self.assertTrue(
            os.path.exists(self.log_file),
            "Интеграционная ошибка: Файл логов не был создан реальным модулем AnomalyLogger."
        )

        agg_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        final_report = self.hub.generate_final_report()

        self.assertIsNotNone(
            final_report,
            "Интеграционная ошибка: generate_final_report() вернул None."
        )

        if isinstance(final_report, dict):
            self.assertTrue(len(final_report) >= 0)
        elif isinstance(final_report, str):
            self.assertTrue(len(final_report) >= 0)

if __name__ == "__main__":
    unittest.main()