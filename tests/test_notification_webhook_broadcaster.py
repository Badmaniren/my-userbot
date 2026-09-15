import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.notification_webhook_broadcaster import NotificationWebhookBroadcaster
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.notification_template_engine import NotificationTemplateEngine

class TestNotificationWebhookBroadcaster(unittest.TestCase):

    def setUp(self):
        self.broadcaster = NotificationWebhookBroadcaster()
        self.random_incident_id = str(uuid.uuid4())
        self.random_severity = random.choice(["CRITICAL", "HIGH", "WARNING", "INFO"])
        self.random_message = ''.join(random.choices(string.ascii_letters + string.whitespace, k=32))
        self.random_channel_name = f"channel_{uuid.uuid4().hex[:8]}"
        self.random_webhook_url = f"https://{uuid.uuid4().hex[:10]}.example.com/webhook"
        self.random_template_name = f"tmpl_{uuid.uuid4().hex[:6]}"

    def test_initialization_composition(self):
        self.assertIsInstance(self.broadcaster.dispatcher, NotificationChannelDispatcher)
        self.assertIsInstance(self.broadcaster.template_engine, NotificationTemplateEngine)

    def test_broadcast_incident_success(self):
        raw_data = {"details": ''.join(random.choices(string.ascii_lowercase, k=16))}
        
        expected_payload = {
            "incident_id": self.random_incident_id,
            "severity": self.random_severity,
            "data": raw_data,
            "rendered_text": "mocked_text_render"
        }
        
        expected_broadcast_result = {
            self.random_channel_name: True
        }

        with patch.object(self.broadcaster.template_engine, 'generate_notification_payload', return_value=expected_payload) as mock_gen, \
             patch.object(self.broadcaster.template_engine, 'render_text', return_value="mocked_text_render") as mock_render, \
             patch.object(self.broadcaster.dispatcher, 'broadcast', return_value=expected_broadcast_result) as mock_broadcast:

            result = self.broadcaster.broadcast_incident(
                self.random_severity, 
                self.random_incident_id, 
                raw_data, 
                self.random_template_name
            )

            mock_gen.assert_called_once_with(self.random_severity, self.random_incident_id, raw_data)
            mock_render.assert_called_once()
            mock_broadcast.assert_called_once()
            self.assertEqual(result, expected_broadcast_result)

    def test_register_and_dispatch_webhook(self):
        config = {"url": self.random_webhook_url, "secret": uuid.uuid4().hex}
        payload = {
            "id": self.random_incident_id,
            "msg": self.random_message
        }

        with patch.object(self.broadcaster.dispatcher, 'register_channel', return_value=True) as mock_register, \
             patch.object(self.broadcaster.dispatcher, 'dispatch', return_value=True) as mock_dispatch:

            reg_res = self.broadcaster.register_webhook_channel(self.random_channel_name, config)
            self.assertTrue(reg_res)
            mock_register.assert_called_once_with(self.random_channel_name, config)

            dispatch_res = self.broadcaster.dispatch_to_webhook(self.random_channel_name, payload)
            self.assertTrue(dispatch_res)
            mock_dispatch.assert_called_once_with(self.random_channel_name, payload)

    def test_process_stream_and_broadcast(self):
        stream_content = f'{{"incident_id": "{self.random_incident_id}", "message": "{self.random_message}"}}'.encode('utf-8')
        mock_stream = io.BytesIO(stream_content)

        parsed_data = {
            "incident_id": self.random_incident_id,
            "message": self.random_message
        }
        
        broadcast_response = {
            uuid.uuid4().hex[:6]: True,
            uuid.uuid4().hex[:6]: False
        }

        with patch.object(self.broadcaster.template_engine, 'parse_stream_data', return_value=parsed_data) as mock_parse_stream, \
             patch.object(self.broadcaster.dispatcher, 'broadcast', return_value=broadcast_response) as mock_broadcast:

            res = self.broadcaster.process_stream_and_broadcast(mock_stream, self.random_severity)

            mock_parse_stream.assert_called_once_with(mock_stream)
            mock_broadcast.assert_called_once()
            self.assertEqual(res, broadcast_response)

    def test_export_notification_report_integration(self):
        context = {
            "incident": self.random_incident_id,
            "error_msg": self.random_message
        }
        random_file_path = f"/tmp/{uuid.uuid4().hex}.html"

        with patch.object(self.broadcaster.template_engine, 'export_notification_file', return_value=True) as mock_export:
            export_res = self.broadcaster.export_notification_report(context, random_file_path)
            
            self.assertTrue(export_res)
            mock_export.assert_called_once_with(context, random_file_path)

    def test_dispatch_failure_handling(self):
        payload = {"alert": self.random_message}
        
        with patch.object(self.broadcaster.dispatcher, 'dispatch', side_effect=Exception("Network failure")) as mock_dispatch:
            with self.assertRaises(Exception):
                self.broadcaster.dispatch_to_webhook(self.random_channel_name, payload)
            mock_dispatch.assert_called_once_with(self.random_channel_name, payload)

if __name__ == '__main__':
    unittest.main()