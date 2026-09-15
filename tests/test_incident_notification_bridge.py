import unittest
from unittest.mock import MagicMock, patch
import json
import os
import io
import random
import uuid
from skills.incident_notification_bridge import IncidentNotificationBridge


class TestIncidentNotificationBridge(unittest.TestCase):

    def setUp(self):
        self.dispatcher_mock = MagicMock()
        self.template_engine_mock = MagicMock()
        self.webhook_broadcaster_mock = MagicMock()
        self.storage_dir = f"temp_storage_{uuid.uuid4().hex}"
        self.bridge = IncidentNotificationBridge(
            dispatcher=self.dispatcher_mock,
            template_engine=self.template_engine_mock,
            webhook_broadcaster=self.webhook_broadcaster_mock,
            storage_dir=self.storage_dir
        )

    def tearDown(self):
        if os.path.exists(self.storage_dir):
            for file_name in os.listdir(self.storage_dir):
                file_path = os.path.join(self.storage_dir, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.storage_dir)

    def test_process_incident_new_and_rendering(self):
        incident_id = uuid.uuid4().hex
        incident_data = {
            "incident_id": incident_id,
            "description": uuid.uuid4().hex,
            "severity": random.choice(["LOW", "MEDIUM", "CRITICAL", "FATAL"])
        }
        channel = uuid.uuid4().hex
        template_name = uuid.uuid4().hex
        rendered_text = uuid.uuid4().hex

        self.template_engine_mock.render.return_value = rendered_text

        result = self.bridge.process_incident(incident_data, channel=channel, template=template_name)

        self.assertTrue(result)
        self.assertIn(incident_id, self.bridge.processed_incidents)
        self.template_engine_mock.render.assert_called_once_with(template_name, incident_data)
        self.dispatcher_mock.dispatch.assert_called_once_with(channel, rendered_text)

    def test_process_incident_duplicate_prevention(self):
        incident_id = uuid.uuid4().hex
        incident_data = {"id": incident_id, "payload": uuid.uuid4().hex}
        channel = uuid.uuid4().hex

        self.template_engine_mock.render_default.return_value = uuid.uuid4().hex

        first_attempt = self.bridge.process_incident(incident_data, channel=channel)
        self.assertTrue(first_attempt)

        second_attempt = self.bridge.process_incident(incident_data, channel=channel)
        self.assertFalse(second_attempt)
        self.dispatcher_mock.dispatch.assert_called_once()

    def test_process_incident_fallback_render_default(self):
        incident_id = uuid.uuid4().hex
        incident_data = {"id": incident_id, "message": uuid.uuid4().hex}
        channel = uuid.uuid4().hex
        default_rendered = uuid.uuid4().hex

        delattr(self.template_engine_mock, "render")
        self.template_engine_mock.render_default.return_value = default_rendered

        result = self.bridge.process_incident(incident_data, channel=channel)

        self.assertTrue(result)
        self.template_engine_mock.render_default.assert_called_once_with(incident_data)
        self.dispatcher_mock.dispatch.assert_called_once_with(channel, default_rendered)

    def test_process_incident_fallback_str(self):
        incident_id = uuid.uuid4().hex
        incident_data = {"id": incident_id, "info": uuid.uuid4().hex}
        channel = uuid.uuid4().hex

        bridge_no_methods = IncidentNotificationBridge(
            dispatcher=self.dispatcher_mock,
            template_engine=object(),
            storage_dir=self.storage_dir
        )

        result = bridge_no_methods.process_incident(incident_data, channel=channel)

        self.assertTrue(result)
        self.dispatcher_mock.dispatch.assert_called_once_with(channel, str(incident_data))

    def test_broadcast_to_webhooks(self):
        webhook_url = f"https://{uuid.uuid4().hex}.com/webhook"
        payload = {"event": uuid.uuid4().hex, "code": random.randint(1000, 9999)}
        expected_response = {"status_code": 200, "body": uuid.uuid4().hex}

        self.webhook_broadcaster_mock.broadcast.return_value = expected_response

        response = self.bridge.broadcast_to_webhooks(webhook_url, payload)

        self.assertEqual(response, expected_response)
        self.webhook_broadcaster_mock.broadcast.assert_called_once_with(webhook_url, payload)

    def test_broadcast_to_webhooks_no_broadcaster(self):
        bridge_naked = IncidentNotificationBridge()
        webhook_url = f"https://{uuid.uuid4().hex}.com/hook"
        payload = {"data": uuid.uuid4().hex}

        response = bridge_naked.broadcast_to_webhooks(webhook_url, payload)

        self.assertEqual(response, {"status_code": 200})

    def test_ingest_stream_bytes(self):
        incident_id = uuid.uuid4().hex
        incident_data = {"incident_id": incident_id, "data": uuid.uuid4().hex}
        stream_content = json.dumps(incident_data).encode('utf-8')
        stream = io.BytesIO(stream_content)
        channel = uuid.uuid4().hex

        with patch.object(self.bridge, 'process_incident', return_value=True) as mock_process:
            result = self.bridge.ingest_stream(stream, channel=channel)
            self.assertTrue(result)
            mock_process.assert_called_once_with(incident_data, channel=channel)

    def test_dispatch_critical_incident_with_storage(self):
        incident_id = uuid.uuid4().hex
        aggregated_incident = {
            "id": incident_id,
            "threat_level": random.choice(["HIGH", "SEVERE", "CRITICAL"]),
            "vector": uuid.uuid4().hex
        }

        result = self.bridge.dispatch_critical_incident(aggregated_incident)

        expected_dict = {
            "dispatch_id": f"dispatch_{incident_id}",
            "incident_id": incident_id,
            "success": True
        }
        self.assertEqual(result, expected_dict)

        file_path = os.path.join(self.storage_dir, f"{incident_id}.json")
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, aggregated_incident)

    def test_dispatch_critical_incident_no_storage_dir(self):
        bridge_no_storage = IncidentNotificationBridge()
        incident_id = uuid.uuid4().hex
        aggregated_incident = {"incident_id": incident_id, "info": uuid.uuid4().hex}

        result = bridge_no_storage.dispatch_critical_incident(aggregated_incident)

        self.assertEqual(result, {
            "dispatch_id": f"dispatch_{incident_id}",
            "incident_id": incident_id,
            "success": True
        })