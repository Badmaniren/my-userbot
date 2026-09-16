import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.incident_notification_broadcaster import IncidentNotificationBroadcaster
from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class TestIncidentNotificationBroadcaster(unittest.TestCase):

    def setUp(self):
        self.mock_bridge = MagicMock(spec=IncidentNotificationBridge)
        self.mock_dispatcher = MagicMock(spec=NotificationChannelDispatcher)
        self.broadcaster = IncidentNotificationBroadcaster(
            bridge=self.mock_bridge,
            dispatcher=self.mock_dispatcher
        )

    def test_broadcast_incident_success(self):
        rand_incident_id = str(uuid.uuid4())
        rand_channel = ''.join(random.choices(string.ascii_lowercase, k=8))
        rand_message = ''.join(random.choices(string.ascii_letters + string.whitespace, k=32))
        rand_level = random.choice(['INFO', 'WARNING', 'CRITICAL', 'ERROR'])

        payload = {
            "incident_id": rand_incident_id,
            "message": rand_message,
            "level": rand_level
        }

        self.mock_dispatcher.format_payload.return_value = payload
        self.mock_dispatcher.broadcast.return_value = {rand_channel: True}
        self.mock_bridge.process_incident.return_value = True

        result = self.broadcaster.broadcast_incident(
            incident_id=rand_incident_id,
            level=rand_level,
            message=rand_message,
            channel=rand_channel
        )

        self.assertIsInstance(result, dict)
        self.assertIn(rand_channel, result)
        self.assertTrue(result[rand_channel])

        self.mock_dispatcher.format_payload.assert_called_once_with(rand_level, rand_incident_id, rand_message)
        self.mock_dispatcher.broadcast.assert_called_once_with(payload)
        self.mock_bridge.process_incident.assert_called_once_with(payload, rand_channel, None)

    def test_ingest_and_broadcast_stream(self):
        rand_stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        rand_channel = ''.join(random.choices(string.ascii_lowercase, k=10))
        stream_mock = io.BytesIO(rand_stream_data)

        parsed_data = {
            "id": str(uuid.uuid4()),
            "status": random.choice(["active", "resolved", "investigating"])
        }
        self.mock_dispatcher.parse_stream_data.return_value = parsed_data
        self.mock_bridge.ingest_stream.return_value = True

        result = self.broadcaster.ingest_and_broadcast_stream(stream_mock, rand_channel)

        self.assertTrue(result)
        self.mock_dispatcher.parse_stream_data.assert_called_once_with(stream_mock)
        self.mock_bridge.ingest_stream.assert_called_once_with(stream_mock, rand_channel)

    def test_dispatch_critical_incident_flow(self):
        rand_incident_id = str(uuid.uuid4())
        rand_title = ''.join(random.choices(string.ascii_letters, k=12))
        aggregated_incident = {
            "incident_id": rand_incident_id,
            "title": rand_title,
            "severity": "CRITICAL"
        }

        self.mock_bridge.dispatch_critical_incident.return_value = {
            "status": "dispatched",
            "id": rand_incident_id
        }

        with patch('skills.incident_notification_broadcaster.datetime') as mock_datetime:
            rand_timestamp = str(random.randint(1000000000, 2000000000))
            mock_datetime.now.return_value.isoformat.return_value = rand_timestamp

            result = self.broadcaster.dispatch_critical(aggregated_incident)

            self.assertEqual(result["id"], rand_incident_id)
            self.assertEqual(result["status"], "dispatched")
            self.mock_bridge.dispatch_critical_incident.assert_called_once_with(aggregated_incident)

    def test_register_new_channel_delegation(self):
        rand_channel_name = ''.join(random.choices(string.ascii_uppercase, k=6))
        rand_webhook_url = f"https://{ ''.join(random.choices(string.ascii_lowercase, k=8)) }.com/webhook"
        config = {"url": rand_webhook_url, "timeout": random.randint(1, 10)}

        self.broadcaster.register_channel(rand_channel_name, config)

        self.mock_dispatcher.register_channel.assert_called_once_with(rand_channel_name, config)

    def test_broadcast_to_webhooks_delegation(self):
        rand_url = f"https://{ ''.join(random.choices(string.ascii_lowercase, k=10)) }.org/api"
        rand_payload = {
            "uuid": str(uuid.uuid4()),
            "metric": random.random()
        }
        
        self.mock_bridge.broadcast_to_webhooks.return_value = random.choice([True, False])

        result = self.broadcaster.broadcast_to_webhooks(rand_url, rand_payload)

        self.assertIsInstance(result, bool)
        self.mock_bridge.broadcast_to_webhooks.assert_called_once_with(rand_url, rand_payload)