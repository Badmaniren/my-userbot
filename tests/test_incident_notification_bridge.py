import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.incident_notification_bridge import IncidentNotificationBridge


class TestIncidentNotificationBridge(unittest.TestCase):

    def setUp(self):
        self.channel_dispatcher = MagicMock()
        self.template_engine = MagicMock()
        self.webhook_broadcaster = MagicMock()
        self.bridge = IncidentNotificationBridge(
            dispatcher=self.channel_dispatcher,
            template_engine=self.template_engine,
            webhook_broadcaster=self.webhook_broadcaster
        )

    def test_process_critical_incident_success(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(['CRITICAL', 'HIGH', 'EMERGENCY'])
        description = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        channel = ''.join(random.choices(string.ascii_lowercase, k=8))
        template_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        rendered_message = ''.join(random.choices(string.ascii_letters + string.punctuation, k=64))

        incident_data = {
            "incident_id": incident_id,
            "severity": severity,
            "description": description
        }

        self.template_engine.render.return_value = rendered_message
        self.channel_dispatcher.dispatch.return_value = True

        result = self.bridge.process_incident(incident_data, channel=channel, template=template_name)

        self.assertTrue(result)
        self.template_engine.render.assert_called_once_with(template_name, incident_data)
        self.channel_dispatcher.dispatch.assert_called_once_with(channel, rendered_message)

    def test_process_incident_deduplication(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(['CRITICAL', 'HIGH'])
        description = ''.join(random.choices(string.ascii_letters, k=20))
        channel = ''.join(random.choices(string.ascii_lowercase, k=6))

        incident_data = {
            "incident_id": incident_id,
            "severity": severity,
            "description": description
        }

        with patch('skills.incident_notification_bridge.time') as mock_time:
            mock_time.time.return_value = random.randint(100000, 999999)
            
            first_result = self.bridge.process_incident(incident_data, channel=channel)
            second_result = self.bridge.process_incident(incident_data, channel=channel)

            self.assertTrue(first_result)
            self.assertFalse(second_result)
            self.assertEqual(self.channel_dispatcher.dispatch.call_count, 1)

    def test_broadcast_incident_via_webhook(self):
        webhook_url = f"https://{ ''.join(random.choices(string.ascii_lowercase, k=10)) }.com/{uuid.uuid4().hex}"
        event_name = ''.join(random.choices(string.ascii_uppercase, k=12))
        payload_value = ''.join(random.choices(string.ascii_letters, k=16))

        incident_payload = {
            "event": event_name,
            "data": payload_value
        }

        self.webhook_broadcaster.broadcast.return_value = {"status_code": 200, "response": uuid.uuid4().hex}

        result = self.bridge.broadcast_to_webhooks(webhook_url, incident_payload)

        self.assertIn("status_code", result)
        self.assertEqual(result["status_code"], 200)
        self.webhook_broadcaster.broadcast.assert_called_once_with(webhook_url, incident_payload)

    def test_stream_incident_from_file_object(self):
        incident_id = uuid.uuid4().hex
        source_data = json.dumps({
            "incident_id": incident_id,
            "severity": "CRITICAL",
            "message": "System meltdown"
        }).encode('utf-8')

        file_stream = io.BytesIO(source_data)
        channel = ''.join(random.choices(string.ascii_lowercase, k=7))

        with patch.object(self.bridge, 'process_incident', return_value=True) as mock_process:
            result = self.bridge.ingest_stream(file_stream, channel=channel)
            
            self.assertTrue(result)
            mock_process.assert_called_once()
            args, _ = mock_process.call_args
            self.assertEqual(args[0]["incident_id"], incident_id)

    def test_dispatcher_failure_handling(self):
        incident_id = uuid.uuid4().hex
        channel = ''.join(random.choices(string.ascii_lowercase, k=5))
        incident_data = {
            "incident_id": incident_id,
            "severity": "CRITICAL",
            "description": "Failure test"
        }

        self.channel_dispatcher.dispatch.side_effect = Exception("Network timeout")

        with self.assertRaises(Exception) as context:
            self.bridge.process_incident(incident_data, channel=channel)

        self.assertIn("Network timeout", str(context.exception))
        self.channel_dispatcher.dispatch.assert_called_once()