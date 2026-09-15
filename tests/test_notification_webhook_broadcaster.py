import unittest
from unittest.mock import patch
import random
import uuid
import string
import io
from skills.notification_webhook_broadcaster import NotificationWebhookBroadcaster

class TestNotificationWebhookBroadcaster(unittest.TestCase):
    def setUp(self):
        self.broadcaster = NotificationWebhookBroadcaster()
        self.template_name = f"template_{uuid.uuid4().hex[:8]}"
        self.channel_name = f"channel_{uuid.uuid4().hex[:8]}"
        self.incident_id = str(uuid.uuid4())
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.context = {
            f"key_{uuid.uuid4().hex[:4]}": ''.join(random.choices(string.ascii_letters, k=10))
            for _ in range(3)
        }
        self.channels = [f"chan_{uuid.uuid4().hex[:4]}" for _ in range(2)]
        self.stream_bytes = io.BytesIO(uuid.uuid4().bytes)
        self.file_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.raw_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.webhook_config = {f"url_{uuid.uuid4().hex[:4]}": f"https://{uuid.uuid4().hex}.com"}

    def test_broadcast_incident_success(self):
        expected_result = {ch: True for ch in self.channels}
        with patch.object(self.broadcaster.template_engine, 'render_text', return_value="rendered_text_payload") as mock_render, \
             patch.object(self.broadcaster.dispatcher, 'broadcast', return_value=expected_result) as mock_broadcast:

            result = self.broadcaster.broadcast_incident(self.template_name, self.context, self.channels)

            mock_render.assert_called_once_with(self.template_name, self.context)
            mock_broadcast.assert_called_once_with("rendered_text_payload", channels=self.channels)
            self.assertEqual(result, expected_result)

    def test_send_to_channel_text(self):
        with patch.object(self.broadcaster.template_engine, 'render_text', return_value="text_content") as mock_render, \
             patch.object(self.broadcaster.dispatcher, 'dispatch', return_value=True) as mock_dispatch:

            result = self.broadcaster.send_to_channel(self.channel_name, self.template_name, self.context, format_type="text")

            mock_render.assert_called_once_with(self.template_name, self.context)
            mock_dispatch.assert_called_once_with(self.channel_name, "text_content")
            self.assertTrue(result)

    def test_send_to_channel_html(self):
        with patch.object(self.broadcaster.template_engine, 'render_html', return_value="<html></html>") as mock_render, \
             patch.object(self.broadcaster.dispatcher, 'dispatch', return_value=True) as mock_dispatch:

            result = self.broadcaster.send_to_channel(self.channel_name, self.template_name, self.context, format_type="HTML")

            mock_render.assert_called_once_with(self.template_name, self.context)
            mock_dispatch.assert_called_once_with(self.channel_name, "<html></html>")
            self.assertTrue(result)

    def test_process_stream_and_broadcast(self):
        parsed_data = {"incident_id": self.incident_id, "status": "active"}
        expected_broadcast = {self.channel_name: True}
        with patch.object(self.broadcaster.template_engine, 'parse_stream_data', return_value=parsed_data) as mock_parse, \
             patch.object(self.broadcaster.dispatcher, 'broadcast', return_value=expected_broadcast) as mock_broadcast:

            result = self.broadcaster.process_stream_and_broadcast(self.stream_bytes, self.template_name)

            mock_parse.assert_called_once_with(self.stream_bytes)
            mock_broadcast.assert_called_once_with(parsed_data)
            self.assertEqual(result, expected_broadcast)

    def test_register_webhook(self):
        with patch.object(self.broadcaster.dispatcher, 'register_channel') as mock_register:
            self.broadcaster.register_webhook(self.channel_name, self.webhook_config)
            mock_register.assert_called_once_with(self.channel_name, self.webhook_config)

    def test_export_artifact(self):
        with patch.object(self.broadcaster.template_engine, 'export_notification_file', return_value=True) as mock_export:
            result = self.broadcaster.export_artifact(self.context, self.file_path)
            mock_export.assert_called_once_with(self.context, self.file_path)
            self.assertTrue(result)

    def test_process_and_broadcast(self):
        payload = {"severity": self.severity, "id": self.incident_id, "data": self.raw_data}
        with patch.object(self.broadcaster.template_engine, 'generate_notification_payload', return_value=payload) as mock_gen, \
             patch.object(self.broadcaster.dispatcher, 'dispatch', return_value=True) as mock_dispatch:

            result = self.broadcaster.process_and_broadcast(self.channel_name, self.severity, self.incident_id, self.raw_data)

            mock_gen.assert_called_once_with(severity=self.severity, incident_id=self.incident_id, raw_data=self.raw_data)
            mock_dispatch.assert_called_once_with(self.channel_name, payload)
            self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()