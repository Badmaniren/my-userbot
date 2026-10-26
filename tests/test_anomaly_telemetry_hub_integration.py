import unittest
import tempfile
import os
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_telemetry_hub import start_new

class TestAnomalyTelemetryHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, f"anomaly_log_{uuid.uuid4()}.json")
        self.repo_path = self.test_dir.name
        self.threshold = random.randint(5, 15)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_telemetry_hub_integration_workflow(self):
        source_id = f"service_{uuid.uuid4()}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"cpu_load_{random.randint(100, 999)}"
        metric_value = random.uniform(10.0, 99.9)

        telemetry_data = {
            "id": str(uuid.uuid4()),
            "source": source_id,
            "metric": metric_name,
            "value": metric_value,
            "status": "active"
        }

        filtered_data = start_new(telemetry_data)
        self.assertIsNotNone(filtered_data, "Фильтр телеметрии не должен возвращать None")

        audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        audit_hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details={"random_payload": str(uuid.uuid4())},
            telemetry_snapshot=filtered_data
        )

        audit_hub.aggregate_and_report(metric_name=metric_name, value=metric_value)
        final_report = audit_hub.generate_final_report()
        self.assertIsNotNone(final_report, "Итоговый отчет не должен быть пустым")

        logger = AnomalyLogger(log_path=self.log_path)
        anomalies = logger.get_anomalies()
        self.assertIsInstance(anomalies, list, "Список аномалий должен быть представлен списком")
        self.assertTrue(len(anomalies) > 0, "Лог должен содержать как минимум одну зарегистрированную аномалию")

        recorded_anomaly = next((a for a in anomalies if a.get("source") == source_id), None)
        self.assertIsNotNone(recorded_anomaly, "Лог должен содержать исходную зарегистрированную аномалию")
        self.assertEqual(recorded_anomaly.get("source"), source_id)
        self.assertEqual(recorded_anomaly.get("severity"), severity_level)

        structured_report = logger.get_structured_report()
        self.assertIsNotNone(structured_report, "Структурированный отчет должен быть сформирован")

        self.assertTrue(os.path.exists(self.log_path), "Файл логов телеметрии и аномалий должен реально существовать на диске")

if __name__ == "__main__":
    unittest.main()
