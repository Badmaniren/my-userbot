import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
import json

from skills.incident_notification_broadcaster import IncidentNotificationBroadcaster
from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class TestIncidentNotificationBroadcaster(unittest.TestCase):

    def setUp(self):
        self.dispatcher_mock = MagicMock(spec=NotificationChannelDispatcher)
        self.bridge_mock = MagicMock(spec=IncidentNotificationBridge)

        self.storage_dir = f"/tmp/{uuid.uuid4().hex}"
        self.webhook_url = f"https://webhook.{uuid.uuid4().hex}.local/notify"

        self.broadcaster = IncidentNotificationBroadcaster(
            dispatcher=self.dispatcher_mock,
            bridge=self.bridge_mock,
            default_webhook=self.webhook_url,
            storage_dir=self.storage_dir
        )

    def test_composition_initialization_and_attributes(self):
        self.assertIsInstance(self.broadcaster.dispatcher, NotificationChannelDispatcher)
        self.assertIsInstance(self.broadcaster.bridge, IncidentNotificationBridge)
        self.assertEqual(self.broadcaster.storage_dir, self.storage_dir)
        self.assertEqual(self.broadcaster.default_webhook, self.webhook_url)

    def test_broadcast_critical_incident_success(self):
        incident_id = uuid.uuid4().hex
        message = "".join(random.choices(string.ascii_letters + " ", k=25))
        level = random.choice(["CRITICAL", "FATAL", "EMERGENCY"])

        aggregated_incident = {
            "id": incident_id,
            "level": level,
            "message": message,
            "timestamp": random.randint(1600000000, 1700000000)
        }

        dispatch_result = {
            f"channel_{uuid.uuid4().hex}": True,
            f"channel_{uuid.uuid4().hex}": True
        }

        self.dispatcher_mock.broadcast.return_value = dispatch_result
        self.bridge_mock.dispatch_critical_incident.return_value = True

        result = self.broadcaster.broadcast_critical_incident_securely(aggregated_incident)

        self.assertTrue(result["success"])
        self.assertEqual(result["broadcast_results"], dispatch_result)
        self.bridge_mock.dispatch_critical_incident.assert_called_once_with(aggregated_incident)
        self.dispatcher_mock.broadcast.assert_called_once()

    def test_broadcast_critical_incident_failure_propagation(self):
        incident_id = uuid.uuid4().hex
        message = "".join(random.choices(string.ascii_letters, k=15))

        aggregated_incident = {
            "id": incident_id,
            "level": "CRITICAL",
            "message": message
        }

        self.bridge_mock.dispatch_critical_incident.side_effect = RuntimeError(f"Error {uuid.uuid4().hex}")

        with self.assertRaises(RuntimeError):
            self.broadcaster.broadcast_critical_incident_securely(aggregated_incident)

        self.bridge_mock.dispatch_critical_incident.assert_called_once_with(aggregated_incident)

    def test_ingest_and_broadcast_stream(self):
        stream_data = {
            "incident_id": uuid.uuid4().hex,
            "metric": random.randint(100, 999),
            "status": uuid.uuid4().hex
        }
        stream_bytes = json.dumps(stream_data).encode("utf-8")
        file_stream = io.BytesIO(stream_bytes)

        channel_name = f"chan_{uuid.uuid4().hex}"
        template_name = f"tmpl_{uuid.uuid4().hex}"

        parsed_stream = {
            "id": stream_data["incident_id"],
            "data": stream_data
        }

        self.dispatcher_mock.parse_stream_data.return_value = parsed_stream
        self.bridge_mock.ingest_stream.return_value = True
        self.dispatcher_mock.dispatch.return_value = True

        res = self.broadcaster.ingest_and_broadcast_stream(file_stream, channel_name, template_name)

        self.assertTrue(res)
        self.dispatcher_mock.parse_stream_data.assert_called_once_with(file_stream)
        self.bridge_mock.ingest_stream.assert_called_once_with(file_stream, channel_name)
        self.dispatcher_mock.dispatch.assert_called_once()

    def test_process_and_webhook_broadcast(self):
        incident_data = {
            "code": random.randint(400, 599),
            "reason": uuid.uuid4().hex
        }
        channel_name = f"channel_{uuid.uuid4().hex}"
        template_name = f"template_{uuid.uuid4().hex}"
        webhook_target = f"https://api.{uuid.uuid4().hex}.net/hook"

        payload = {
            "payload_id": uuid.uuid4().hex,
            "data": incident_data
        }

        self.bridge_mock.process_incident.return_value = payload
        self.bridge_mock.broadcast_to_webhooks.return_value = {"status_code": 200, "success": True}

        output = self.broadcaster.process_and_webhook_broadcast(incident_data, channel_name, template_name, webhook_target)

        self.assertTrue(output["success"])
        self.assertEqual(output["payload"], payload)
        self.bridge_mock.process_incident.assert_called_once_with(incident_data, channel_name, template_name)
        self.bridge_mock.broadcast_to_webhooks.assert_called_once_with(webhook_target, payload)

    def test_register_channel_via_broadcaster(self):
        channel_name = f"channel_{uuid.uuid4().hex}"
        config = {
            "endpoint": f"https://{uuid.uuid4().hex}.com",
            "token": uuid.uuid4().hex,
            "timeout": random.randint(5, 30)
        }

        self.broadcaster.register_notification_channel(channel_name, config)

        self.dispatcher_mock.register_channel.assert_called_once_with(channel_name, config)