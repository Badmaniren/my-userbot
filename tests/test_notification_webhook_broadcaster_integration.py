import unittest
import uuid
import random
import os
import json
from skills.notification_webhook_broadcaster import NotificationWebhookBroadcaster


class TestNotificationWebhookBroadcasterIntegration(unittest.TestCase):

    def setUp(self):
        self.broadcaster = NotificationWebhookBroadcaster()
        self.channel_name = f"test_channel_{uuid.uuid4().hex[:8]}"
        self.template_name = f"template_{uuid.uuid4().hex[:8]}"
        self.incident_id = str(uuid.uuid4())
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.random_port = random.randint(1024, 65535)

        self.config = {
            "url": f"http://127.0.0.1:{self.random_port}/webhook",
            "method": "POST"
        }
        self.context = {
            "incident_id": self.incident_id,
            "severity": self.severity,
            "message": f"Random error message {uuid.uuid4().hex}"
        }

    def test_webhook_broadcaster_end_to_end(self):
        self.broadcaster.register_webhook(self.channel_name, self.config)

        broadcast_result = self.broadcaster.broadcast_incident(
            template_name=self.template_name,
            context=self.context,
            channels=[self.channel_name]
        )
        self.assertIsInstance(broadcast_result, dict)

        send_result = self.broadcaster.send_to_channel(
            channel_name=self.channel_name,
            template_name=self.template_name,
            context=self.context,
            format_type="text"
        )
        self.assertIsInstance(send_result, bool)

        html_send_result = self.broadcaster.send_to_channel(
            channel_name=self.channel_name,
            template_name=self.template_name,
            context=self.context,
            format_type="html"
        )
        self.assertIsInstance(html_send_result, bool)

        stream_data = json.dumps({
            "stream_id": str(uuid.uuid4()),
            "status": "active",
            "metric": random.random()
        }).encode("utf-8")

        stream_result = self.broadcaster.process_stream_and_broadcast(
            stream_bytes=stream_data,
            template_name=self.template_name
        )
        self.assertIsInstance(stream_result, dict)

        file_path = f"artifact_{uuid.uuid4().hex}.txt"
        try:
            export_result = self.broadcaster.export_artifact(
                context=self.context,
                file_path=file_path
            )
            self.assertIsInstance(export_result, bool)
            if export_result:
                self.assertTrue(os.path.exists(file_path))
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

        process_broadcast_result = self.broadcaster.process_and_broadcast(
            channel_name=self.channel_name,
            severity=self.severity,
            incident_id=self.incident_id,
            raw_data=self.context
        )
        self.assertIsInstance(process_broadcast_result, bool)


if __name__ == "__main__":
    unittest.main()