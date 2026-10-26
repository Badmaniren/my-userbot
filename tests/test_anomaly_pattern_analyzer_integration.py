import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_pattern_analyzer import *
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyPatternAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, f"test_log_{uuid.uuid4()}.json")
        self.repo_path = self.test_dir.name
        self.threshold = random.randint(5, 15)
        
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.logger = AnomalyLogger(log_path=self.log_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pattern_analyzer_integration_flow(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = random.uniform(10.0, 100.0)
        
        telemetry_data = {
            "cpu_usage": random.randint(40, 99),
            "memory_leak_detected": random.choice([True, False]),
            "request_id": str(uuid.uuid4())
        }
        
        details_text = f"Pattern anomaly detected with random payload ID: {uuid.uuid4()}"

        self.logger.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details_text,
            telemetry_snapshot=telemetry_data
        )

        anomalies_list = self.logger.get_anomalies()
        self.assertGreaterEqual(len(anomalies_list), 1, "Логгер должен зафиксировать аномалию")

        logged_entry = anomalies_list[-1]
        self.assertEqual(logged_entry.get("source"), source_id)
        self.assertEqual(logged_entry.get("severity"), severity_level)
        self.assertEqual(logged_entry.get("details"), details_text)

        self.audit_hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details_text,
            telemetry_snapshot=telemetry_data
        )

        self.audit_hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        final_report = self.audit_hub.generate_final_report()
        self.assertIsInstance(final_report, (dict, str, list), "Финальный отчет должен быть сформирован")

        structured_report = self.logger.get_structured_report()
        self.assertIsNotNone(structured_report, "Структурированный отчет не должен быть пустым")

        self.assertTrue(os.path.exists(self.log_path), "Файл логов должен реально существовать на диске")
        
        file_size = os.path.getsize(self.log_path)
        self.assertGreater(file_size, 0, "Файл логов не должен быть пустым после записи")

if __name__ == "__main__":
    unittest.main()