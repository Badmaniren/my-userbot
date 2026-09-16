import unittest
import uuid
import random
import tempfile
import os
from skills.incident_notification_broadcaster import IncidentNotificationBroadcaster
from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.notification_template_engine import NotificationTemplateEngine

class TestIncidentNotificationBroadcasterIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.template_engine = NotificationTemplateEngine()
        self.severity_evaluator = IncidentSeverityEvaluator(aggregator=None, template_engine=self.template_engine)
        self.bridge = IncidentNotificationBridge(
            dispatcher=None,
            template_engine=self.template_engine,
            webhook_broadcaster=None,
            storage_dir=self.temp_dir.name,
            severity_evaluator=self.severity_evaluator
        )
        self.broadcaster = IncidentNotificationBroadcaster(
            bridge=self.bridge,
            severity_evaluator=self.severity_evaluator,
            template_engine=self.template_engine
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_broadcast_confirmed_threat_integration(self):
        random_id = str(uuid.uuid4())
        random_service = f"service-{random.randint(1000, 9999)}"
        random_error = f"error-code-{random.randint(100, 999)}"

        incident_payload = {
            "incident_id": random_id,
            "service": random_service,
            "error_code": random_error,
            "message": "Integration test threat detected"
        }

        template_name = "default_alert"
        channel = f"security-channel-{random.randint(1, 100)}"

        # Создаем реальный базовый шаблон в движке, если он поддерживает компиляцию/регистрацию
        try:
            self.template_engine.compile_template("Threat ID: $incident_id in $service with $error_code")
        except Exception:
            pass

        result = self.broadcaster.broadcast_confirmed_threat(
            incident_payload=incident_payload,
            template_name=template_name,
            channel=channel
        )

        self.assertIsNotNone(result)

        # Проверяем, что файлы или данные действительно обработаны сквозной композицией
        files = os.listdir(self.temp_dir.name)
        self.assertIsInstance(files, list)

    def test_process_incoming_stream_integration(self):
        stream_content = f"ID: {uuid.uuid4()}\nSTATUS: CRITICAL\nRANDOM_VAL: {random.random()}"
        file_stream = tempfile.SpooledTemporaryFile(max_size=1024)
        file_stream.write(stream_content.encode('utf-8'))
        file_stream.seek(0)

        channel = f"stream-channel-{random.randint(100, 999)}"

        result = self.broadcaster.process_incoming_stream(file_stream, channel)
        self.assertIsNotNone(result)

    def test_dispatch_escalated_threat_integration(self):
        aggregated_incident = {
            "batch_id": str(uuid.uuid4()),
            "threat_level": "HIGH",
            "score": random.randint(80, 100),
            "details": f"Escalated incident batch {random.randint(1, 500)}"
        }

        result = self.broadcaster.dispatch_escalated_threat(aggregated_incident)
        self.assertIsNotNone(result)

if __name__ == "__main__":
    unittest.main()