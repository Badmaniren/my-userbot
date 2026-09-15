import unittest
import uuid
import random
from skills.notification_template_engine import NotificationTemplateEngine
from skills.notification_channel_dispatcher import NotificationChannelDispatcher

class TestNotificationTemplateEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.engine = NotificationTemplateEngine()
        self.channel_name = f"channel_{uuid.uuid4().hex[:8]}"
        self.incident_id = f"INC-{random.randint(1000, 9999)}"
        self.error_message = f"Error occurred during self-healing: {uuid.uuid4().hex[:6]}"

    def test_send_templated_integration(self):
        payload = {
            "id": self.incident_id,
            "msg": self.error_message,
            "severity": "CRITICAL"
        }

        result = self.engine.send_templated(self.channel_name, payload)

        self.assertTrue(result, "Диспетчер должен успешно отправить сообщение через канал")
        self.assertIn(self.channel_name, self.engine.dispatcher.channels, "Канал должен быть автоматически зарегистрирован движком")

        channel_config = self.engine.dispatcher.channels[self.channel_name]
        self.assertEqual(channel_config.get("endpoint"), "mock://internal")

    def test_broadcast_template_integration(self):
        epic_id = f"EPIC-{uuid.uuid4().hex[:8]}"
        details_msg = f"System recovery report summary {random.randint(100, 999)}"

        payload = {
            "epic_id": epic_id,
            "details": details_msg,
            "level": "WARNING"
        }

        broadcast_results = self.engine.broadcast_template(payload)

        self.assertIsInstance(broadcast_results, dict, "Широковещательная рассылка должна возвращать словарь результатов")
        self.assertTrue(len(broadcast_results) > 0, "Должен быть задействован хотя бы один канал рассылки")

        for ch_name, success in broadcast_results.items():
            self.assertTrue(success, f"Канал {ch_name} должен вернуть успешный статус доставки")

    def test_format_payload_and_dispatch_pipeline(self):
        self.engine.dispatcher.register_channel(self.channel_name, {"endpoint": "mock://internal"})
        level = random.choice(["INFO", "WARNING", "ERROR", "CRITICAL"])
        formatted = self.engine.format_payload(level, self.incident_id, self.error_message)

        self.assertIsInstance(formatted, dict)
        self.assertEqual(formatted.get("incident_id"), self.incident_id)
        self.assertEqual(formatted.get("level"), level)
        self.assertEqual(formatted.get("message"), self.error_message)

        dispatch_result = self.engine.dispatcher.dispatch(self.channel_name, formatted)
        self.assertTrue(dispatch_result)

if __name__ == '__main__':
    unittest.main()