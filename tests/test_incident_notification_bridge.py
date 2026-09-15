import unittest
from unittest.mock import MagicMock, patch
import io
import json
import os
import random
import uuid
from skills.incident_notification_bridge import IncidentNotificationBridge, IncidentIncidentNotificationBridge


class TestIncidentNotificationBridge(unittest.TestCase):

    def setUp(self):
        self.mock_dispatcher = MagicMock()
        self.mock_template_engine = MagicMock()
        self.mock_webhook_broadcaster = MagicMock()
        self.mock_severity_evaluator = MagicMock()
        self.storage_dir = f"temp_storage_{uuid.uuid4().hex}"
        
        self.bridge = IncidentNotificationBridge(
            dispatcher=self.mock_dispatcher,
            template_engine=self.mock_template_engine,
            webhook_broadcaster=self.mock_webhook_broadcaster,
            storage_dir=self.storage_dir,
            severity_evaluator=self.mock_severity_evaluator
        )

    def tearDown(self):
        if os.path.exists(self.storage_dir):
            for filename in os.listdir(self.storage_dir):
                file_path = os.path.join(self.storage_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.storage_dir)

    def test_process_incident_new(self):
        incident_id = uuid.uuid4().hex
        incident_data = {
            "incident_id": incident_id,
            "message": f"msg_{uuid.uuid4().hex}"
        }
        channel = f"channel_{uuid.uuid4().hex}"
        template = f"template_{uuid.uuid4().hex}"
        
        rendered_msg = f"rendered_{uuid.uuid4().hex}"
        self.mock_template_engine.render.return_value = rendered_msg

        result = self.bridge.process_incident(incident_data, channel=channel, template=template)

        self.assertTrue(result)
        self.mock_template_engine.render.assert_called_once_with(template, incident_data)
        self.mock_dispatcher.dispatch.assert_called_once_with(channel, rendered_msg)
        self.assertIn(incident_id, self.bridge.processed_incidents)

    def test_process_incident_duplicate(self):
        incident_id = uuid.uuid4().hex
        incident_data = {"id": incident_id}
        
        result_first = self.bridge.process_incident(incident_data)
        result_second = self.bridge.process_incident(incident_data)

        self.assertTrue(result_first)
        self.assertFalse(result_second)

    def test_process_incident_default_template(self):
        incident_id = uuid.uuid4().hex
        incident_data = {"incident_id": incident_id, "data": random.randint(1, 100)}
        
        del self.mock_template_engine.render
        self.mock_template_engine.render_default.return_value = f"default_{uuid.uuid4().hex}"

        result = self.bridge.process_incident(incident_data)

        self.assertTrue(result)
        self.mock_template_engine.render_default.assert_called_once_with(incident_data)

    def test_broadcast_to_webhooks(self):
        webhook_url = f"https://webhook.{uuid.uuid4().hex}.com/notify"
        payload = {"event": uuid.uuid4().hex, "code": random.randint(200, 500)}
        expected_response = {"status_code": 200, "uuid": uuid.uuid4().hex}
        
        self.mock_webhook_broadcaster.broadcast.return_value = expected_response

        result = self.bridge.broadcast_to_webhooks(webhook_url, payload)

        self.assertEqual(result, expected_response)
        self.mock_webhook_broadcaster.broadcast.assert_called_once_with(webhook_url, payload)

    def test_broadcast_to_webhooks_no_broadcaster(self):
        bridge_no_bc = IncidentNotificationBridge(webhook_broadcaster=None)
        webhook_url = f"https://webhook.{uuid.uuid4().hex}.com/notify"
        payload = {"data": uuid.uuid4().hex}

        result = bridge_no_bc.broadcast_to_webhooks(webhook_url, payload)

        self.assertEqual(result, {"status_code": 200})

    def test_ingest_stream(self):
        incident_id = uuid.uuid4().hex
        incident_data = {"incident_id": incident_id, "payload": uuid.uuid4().hex}
        json_bytes = json.dumps(incident_data).encode('utf-8')
        file_stream = io.BytesIO(json_bytes)
        channel = f"chan_{uuid.uuid4().hex}"

        result = self.bridge.ingest_stream(file_stream, channel=channel)

        self.assertTrue(result)
        self.assertIn(incident_id, self.bridge.processed_incidents)

    def test_dispatch_critical_incident_with_severity(self):
        incident_id = uuid.uuid4().hex
        aggregated_incident = {
            "id": incident_id,
            "message": f"err_{uuid.uuid4().hex}",
            "traceback_str": f"tb_{uuid.uuid4().hex}"
        }
        severity_result = {"severity": random.choice(["HIGH", "CRITICAL", "MEDIUM"]), "score": random.random()}
        self.mock_severity_evaluator.evaluate.return_value = severity_result

        result = self.bridge.dispatch_critical_incident(aggregated_incident)

        self.assertTrue(result["success"])
        self.assertEqual(result["incident_id"], incident_id)
        self.assertEqual(aggregated_incident["severity_assessment"], severity_result)
        
        file_path = os.path.join(self.storage_dir, f"{incident_id}.json")
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data["id"], incident_id)

    def test_dispatch_critical_incident_eval_exception(self):
        incident_id = uuid.uuid4().hex
        aggregated_incident = {
            "incident_id": incident_id,
            "message": f"fail_{uuid.uuid4().hex}"
        }
        self.mock_severity_evaluator.evaluate.side_effect = Exception(uuid.uuid4().hex)

        result = self.bridge.dispatch_critical_incident(aggregated_incident)

        self.assertTrue(result["success"])
        self.assertEqual(aggregated_incident["severity_assessment"], {"severity": "HIGH"})

    def test_alias_class_instantiation(self):
        alias_bridge = IncidentIncidentNotificationBridge()
        self.assertIsInstance(alias_bridge, IncidentNotificationBridge)