import unittest
import uuid
import random
import tempfile
import os
from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.incident_notification_broadcaster import IncidentNotificationBroadcaster

class SimpleTemplateEngine:
    def __init__(self):
        self.rendered_data = []

    def render(self, data: dict):
        self.rendered_data.append(data)
        return f"Rendered: {data.get('incident_id')}"

class TestIncidentNotificationBroadcasterIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dispatcher = NotificationChannelDispatcher()

        self.channel_name = f"channel_{uuid.uuid4().hex[:8]}"
        self.dispatcher.register_channel(self.channel_name, {"type": "test", "target": "memory"})

        self.template_engine = SimpleTemplateEngine()
        self.bridge = IncidentNotificationBridge(
            dispatcher=self.dispatcher,
            template_engine=self.template_engine,
            webhook_broadcaster=None,
            storage_dir=self.temp_dir.name,
            severity_evaluator=None
        )
        self.broadcaster = IncidentNotificationBroadcaster(
            bridge=self.bridge,
            dispatcher=self.dispatcher
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_execute_broadcast_integration(self):
        incident_id = str(uuid.uuid4())
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        incident_data = {
            "incident_id": incident_id,
            "level": severity_level,
            "message": f"Test message {uuid.uuid4().hex}"
        }

        result = self.broadcaster.execute_broadcast(
            incident_data=incident_data,
            channel=self.channel_name,
            template="standard_alert"
        )

        self.assertIsInstance(result, dict)
        self.assertIn(self.channel_name, result)
        self.assertTrue(result[self.channel_name])

        self.assertEqual(len(self.template_engine.rendered_data), 1)
        self.assertEqual(self.template_engine.rendered_data[0]["incident_id"], incident_id)

        files = os.listdir(self.temp_dir.name)
        self.assertGreaterEqual(len(files), 1)

    def test_broadcast_incident_with_external_template(self):
        incident_id = str(uuid.uuid4())
        payload = {
            "incident_id": incident_id,
            "metric": random.randint(100, 999)
        }

        result = self.broadcaster.broadcast_incident(
            payload_data=payload,
            channel=self.channel_name,
            template_engine=self.template_engine
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(len(self.template_engine.rendered_data), 1)
        self.assertEqual(self.template_engine.rendered_data[0]["metric"], payload["metric"])

if __name__ == "__main__":
    unittest.main()