import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
string_lib = string = __import__('string')

from skills.incident_notification_broadcaster import IncidentNotificationBroadcaster
from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class TestIncidentNotificationBroadcaster(unittest.TestCase):

    def setUp(self):
        self.rand_str = lambda: ''.join(random.choices(string_lib.ascii_lowercase, k=8))
        self.channel_name = f"channel_{self.rand_str()}"
        self.webhook_url = f"https://{self.rand_str()}.com/webhook/{uuid.uuid4().hex}"
        self.incident_id = uuid.uuid4().hex

        self.mock_bridge = MagicMock(spec=IncidentNotificationBridge)
        self.mock_dispatcher = MagicMock(spec=NotificationChannelDispatcher)
        self.mock_template_engine = MagicMock()

        self.mock_bridge.dispatcher = self.mock_dispatcher
        self.broadcaster = IncidentNotificationBroadcaster(
            bridge=self.mock_bridge,
            dispatcher=self.mock_dispatcher
        )

    def test_init_with_default_dispatcher(self):
        broadcaster = IncidentNotificationBroadcaster(bridge=self.mock_bridge)
        self.assertEqual(broadcaster.dispatcher, self.mock_bridge.dispatcher)

    def test_broadcast_incident_with_template(self):
        payload = {uuid.uuid4().hex: self.rand_str()}
        expected_result = {self.channel_name: random.choice([True, False])}
        self.mock_dispatcher.broadcast.return_value = expected_result

        result = self.broadcaster.broadcast_incident(
            payload_data=payload,
            channel=self.channel_name,
            template_engine=self.mock_template_engine
        )

        self.mock_template_engine.render.assert_called_once_with(payload)
        self.mock_dispatcher.broadcast.assert_called_once_with(payload)
        self.assertEqual(result, expected_result)

    def test_broadcast_incident_without_template(self):
        payload = {uuid.uuid4().hex: self.rand_str()}
        expected_result = {self.channel_name: True}
        self.mock_dispatcher.broadcast.return_value = expected_result

        result = self.broadcaster.broadcast_incident(
            payload_data=payload,
            channel=self.channel_name,
            template_engine=None
        )

        self.mock_template_engine.render.assert_not_called()
        self.mock_dispatcher.broadcast.assert_called_once_with(payload)
        self.assertEqual(result, expected_result)

    def test_process_stream_broadcast(self):
        stream_content = f"stream_data_{self.rand_str()}".encode('utf-8')
        stream = io.BytesIO(stream_content)
        expected_response = {uuid.uuid4().hex: random.randint(1, 100)}
        self.mock_bridge.ingest_stream.return_value = expected_response

        result = self.broadcaster.process_stream_broadcast(stream, self.channel_name)

        self.mock_bridge.ingest_stream.assert_called_once_with(stream, self.channel_name)
        self.assertEqual(result, expected_response)

    def test_handle_critical_broadcast(self):
        aggregated_payload = {uuid.uuid4().hex: self.incident_id}
        expected_response = random.choice([True, False])
        self.mock_bridge.dispatch_critical_incident.return_value = expected_response

        result = self.broadcaster.handle_critical_broadcast(aggregated_payload)

        self.mock_bridge.dispatch_critical_incident.assert_called_once_with(aggregated_payload)
        self.assertEqual(result, expected_response)

    def test_forward_to_webhook(self):
        payload_dict = {uuid.uuid4().hex: self.rand_str()}
        expected_response = random.choice([True, False])
        self.mock_bridge.broadcast_to_webhooks.return_value = expected_response

        result = self.broadcaster.forward_to_webhook(self.webhook_url, payload_dict)

        self.mock_bridge.broadcast_to_webhooks.assert_called_once_with(self.webhook_url, payload_dict)
        self.assertEqual(result, expected_response)

    def test_execute_broadcast_pipeline(self):
        incident_data = {uuid.uuid4().hex: self.incident_id}
        template_name = f"template_{self.rand_str()}"
        expected_broadcast_result = {self.channel_name: True}

        self.mock_bridge.template_engine = self.mock_template_engine
        self.mock_dispatcher.broadcast.return_value = expected_broadcast_result

        result = self.broadcaster.execute_broadcast(
            incident_data=incident_data,
            channel=self.channel_name,
            template=template_name
        )

        self.mock_template_engine.render.assert_called_once_with(incident_data)
        self.mock_dispatcher.broadcast.assert_called_once_with(incident_data)
        self.mock_bridge.persist_incident.assert_called_once_with(incident_data)
        self.assertEqual(result, expected_broadcast_result)


if __name__ == '__main__':
    unittest.main()