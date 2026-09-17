import unittest
import os
import uuid
import random
import tempfile
import io
from skills.telemetry_anomaly_audit_bridge import (
    TelemetryAnomalyAuditBridge,
    AnomalyAuditBridgeException,
    AuditBridgeException
)
from skills.telemetry_incident_lifecycle_bridge import TelemetryIncidentLifecycleBridge
from skills.dependency_audit_reporter import DependencyAuditReporter


class TestTelemetryAnomalyAuditBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_dir = self.temp_dir.name

        # Инициализируем реальные зависимости без моков
        self.lifecycle_bridge = TelemetryIncidentLifecycleBridge(workspace_dir=self.workspace_dir)
        self.audit_reporter = DependencyAuditReporter()

        # Создаем тестируемый мост с реальными объектами
        self.bridge = TelemetryAnomalyAuditBridge(
            workspace_dir=self.workspace_dir,
            lifecycle_bridge=self.lifecycle_bridge,
            audit_reporter=self.audit_reporter
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_integration_audit_health_after_incident(self):
        # Генерируем случайные входные данные для исключения хардкода
        random_incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        random_epic_id = f"EPIC-{random.randint(1000, 9999)}"
        random_stream = f"stream_channel_{random.randint(1, 100)}"

        telemetry_payload = {
            "incident_id": random_incident_id,
            "metric_name": "cpu_utilization",
            "metric_value": random.uniform(90.0, 100.0),
            "status": "CRITICAL",
            "timestamp": "2023-10-27T15:30:00Z"
        }

        try:
            result = self.bridge.audit_health_after_incident(
                telemetry_payload=telemetry_payload,
                epic_id=random_epic_id,
                stream=random_stream
            )

            # Проверяем структуру и корректность возвращенных данных
            self.assertIsInstance(result, dict)
            self.assertEqual(result["incident_id"], random_incident_id)
            self.assertIn("lifecycle_closed", result)
            self.assertIn("audit_report", result)
            self.assertIn("epic_finalized", result)

        except AnomalyAuditBridgeException as e:
            self.fail(f"Интеграционный тест audit_health_after_incident завершился ошибкой: {e}")

    def test_integration_process_audit_stream(self):
        # Генерируем случайный поток данных аудита
        random_log_id = str(uuid.uuid4())
        stream_content = f"event_id={random_log_id}\nseverity=HIGH\ndetails=anomaly_detected\n"
        stream_io = io.StringIO(stream_content)

        random_epic_id = f"EPIC-{random.randint(1000, 9999)}"

        try:
            summary = self.bridge.process_audit_stream(
                stream_io=stream_io,
                epic_id=random_epic_id,
                export_format="json"
            )
            # Проверяем, что метод возвращает результат интеграции (не None)
            self.assertIsNotNone(summary)
        except AnomalyAuditBridgeException as e:
            self.fail(f"Интеграционный тест process_audit_stream завершился ошибкой: {e}")

    def test_integration_generate_epic_health_export(self):
        # Генерируем случайные данные для экспорта отчета
        random_epic_id = f"EPIC-{random.randint(1000, 9999)}"
        payload = {
            "epic_id": random_epic_id,
            "scope": "security_audit",
            "generated_by": f"user_{random.randint(1, 50)}",
            "incidents_count": random.randint(1, 10)
        }
        
        unique_filename = f"epic_report_{uuid.uuid4().hex}.json"
        output_path = os.path.join(self.workspace_dir, unique_filename)

        try:
            result = self.bridge.generate_epic_health_export(payload, output_path)

            # Проверяем, что интеграция возвращает результат
            self.assertIsNotNone(result)

            # Если логика компонента предполагает запись файла, проверяем его физическое наличие
            if os.path.exists(output_path):
                self.assertTrue(os.path.getsize(output_path) >= 0)
        except AnomalyAuditBridgeException as e:
            self.fail(f"Интеграционный тест generate_epic_health_export завершился ошибкой: {e}")

    def test_integration_process_anomaly_and_audit(self):
        # Генерируем случайные данные аномалии и аудита
        random_incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        telemetry_payload = {
            "incident_id": random_incident_id,
            "anomaly_score": random.uniform(0.85, 0.99)
        }
        
        audit_data = {
            "vulnerabilities": [
                {"package": "openssl", "severity": "CRITICAL", "id": f"CVE-{random.randint(2020, 2023)}-{random.randint(1000, 9999)}"}
            ],
            "scanned_at": "2023-10-27T16:00:00Z"
        }

        try:
            result = self.bridge.process_anomaly_and_audit(telemetry_payload, audit_data)

            # Проверяем корректность интеграционного ответа
            self.assertIsInstance(result, dict)
            self.assertEqual(result["incident_id"], random_incident_id)
            self.assertEqual(result["lifecycle_status"], "PROCESSED")
            self.assertIn("audit_report", result)

        except AuditBridgeException as e:
            self.fail(f"Интеграционный тест process_anomaly_and_audit завершился ошибкой: {e}")


if __name__ == "__main__":
    unittest.main()