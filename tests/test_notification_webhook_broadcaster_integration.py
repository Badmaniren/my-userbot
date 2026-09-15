import unittest
import uuid
import random
import os
from skills.notification_webhook_broadcaster import NotificationWebhookBroadcaster
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.notification_template_engine import NotificationTemplateEngine

class TestNotificationWebhookBroadcasterIntegration(unittest.TestCase):
    def setUp(self):
        self.broadcaster = NotificationWebhookBroadcaster()
        self.incident_id = str(uuid.uuid4())
        self.severity = random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"])
        self.message = f"Integration test failure message {random.randint(1000, 9999)}"
        self.channel_name = f"webhook_channel_{random.randint(1, 100)}"
        self.channel_config = {"url": f"https://api.test-webhook.local/v1/{uuid.uuid4()}", "timeout": 5}

    def test_real_composition_flow(self):
        self.assertIsInstance(self.broadcaster.dispatcher, NotificationChannelDispatcher)
        self.assertIsInstance(self.broadcaster.template_engine, NotificationTemplateEngine)

        self.broadcaster.dispatcher.register_channel(self.channel_name, self.channel_config)
        
        raw_payload = self.broadcaster.template_engine.generate_notification_payload(
            self.severity, self.incident_id, {"details": self.message}
        )
        
        self.assertIn("incident_id", raw_payload)
        self.assertEqual(raw_payload["incident_id"], self.incident_id)

        broadcast_result = self.broadcaster.dispatcher.broadcast(raw_payload)
        self.assertIsInstance(broadcast_result, dict)
        self.assertIn(self.channel_name, broadcast_result)

if __name__ == "__main__":
    unittest.main()