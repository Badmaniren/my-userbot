import unittest
from unittest.mock import MagicMock, patch
import io
import json
import os
import random
import uuid
from skills.incident_notification_bridge import IncidentIncidentNotificationBridge


class TestIncidentNotificationBridge(unittest.TestCase):
    def setUp(self):
        self.mock_dispatcher = MagicMock()
        self.mock_template_engine = MagicMock()
        self.mock_webhook_broadcaster = MagicMock()
        self.random_storage = f"/tmp/{uuid.uuid4().hex}"
        
        self.bridge = IncidentIncidentNotificationBridge(
            dispatcher=self.mock_dispatcher,
            template_engine=self.mock_template_engine,
            webhook_broadcaster=self.mock_webhook_broadcaster,
            storage_dir=self.random_storage
        )

    def tearDown(self):
        if os.path.exists(self.random_storage):
            for f in os.listdir(self.random_storage):
                file_path = os.path.join(self.random_storage, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.random_storage)

    def test_process_incident_new_id(self):
        incident_id = uuid.uuid4().hex
        channel_name = uuid.uuid4().hex
        template_name = uuid.uuid4().hex
        rendered_text = uuid.uuid4().hex
        
        incident_data = {
            "incident_id": incident_id,
            "payload": uuid.uuid4().hex
        }
        
        self.mock_template_engine.render.return_value = rendered_text

        result = self.bridge.process_incident(incident_data, channel=channel_name, template=template_name)

        self.assertTrue(result)
        self.mock_template_engine.render.assert_called_once_with(template_name, incident_data)
        self.mock_dispatcher.dispatch.assert_called_once_with(channel_name, rendered_text)
        self.assertIn(incident_id, self.bridge.processed_incidents)

    def test_process_incident_duplicate_id(self):
        incident_id = uuid.uuid4().hex
        incident_data = {
            "id": incident_id,
            "metric": random.randint(1, 100)
        }

        first_result = self.bridge.process_incident(incident_data)
        self.assertTrue(first_result)

        second_result = self.bridge.process_incident(incident_data)
        self.assertFalse(second_result)

    def test_process_incident_default_render(self):
        incident_id = uuid.uuid4().hex
        incident_data = {
            "incident_id": incident_id,
            "reason": uuid.uuid4().hex
        }

        self.mock_template_engine.render_default = MagicMock(return_value=uuid.uuid4().hex)
        delattr(self.bridge, "template_engine")
        
        self.bridge.template_engine = self.mock_template_engine
        
        result = self.bridge.process_incident(incident_data)
        self.assertTrue(result)
        self.mock_template_engine.render_default.assert_called_once_with(incident_data)

    def test_broadcast_to_webhooks_active(self):
        webhook_url = f"https://{uuid.uuid4().hex}.com/webhook"
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_response = {"status_code": random.choice([200, 201, 202]), "uuid": uuid.uuid4().hex}
        
        self.mock_webhook_broadcaster.broadcast.return_value = expected_response

        result = self.bridge.broadcast_to_webhooks(webhook_url, payload)

        self.assertEqual(result, expected_response)
        self.mock_webhook_broadcaster.broadcast.assert_called_once_with(webhook_url, payload)

    def test_broadcast_to_webhooks_none(self):
        self.bridge.webhook_broadcaster = None
        webhook_url = f"https://{uuid.uuid4().hex}.org/hook"
        payload = {uuid.uuid4().hex: random.randint(100, 999)}

        result = self.bridge.broadcast_to_webhooks(webhook_url, payload)

        self.assertEqual(result, {"status_code": 200})

    def test_ingest_stream(self):
        incident_id = uuid.uuid4().hex
        raw_data = json.dumps({
            "incident_id": incident_id,
            "data": uuid.uuid4().hex
        }).encode('utf-8')
        
        stream = io.BytesIO(raw_data)
        channel_name = uuid.uuid4().hex

        with patch.object(self.bridge, 'process_incident', return_value=True) as mock_process:
            result = self.bridge.ingest_stream(stream, channel=channel_name)
            
            self.assertTrue(result)
            mock_process.assert_called_once()
            args, kwargs = mock_process.call_args
            self.assertEqual(args[0]["incident_id"], incident_id)
            self.assertEqual(kwargs["channel"], channel_name)

    def test_dispatch_critical_incident(self):
        incident_id = uuid.uuid4().hex
        aggregated_incident = {
            "id": incident_id,
            "severity": uuid.uuid4().hex,
            "score": random.random()
        }

        result = self.bridge.dispatch_critical_incident(aggregated_incident)

        self.assertTrue(result["success"])
        self.assertEqual(result["incident_id"], incident_id)
        self.assertEqual(result["dispatch_id"], f"dispatch_{incident_id}")

        expected_file_path = os.path.join(self.random_storage, f"{incident_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))
        
        with open(expected_file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            self.assertEqual(loaded_data["id"], incident_id)


if __name__ == '__main__':
    unittest.main()