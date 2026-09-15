import unittest
import uuid
import random
import os
import json
import tempfile
from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.notification_template_engine import NotificationTemplateEngine
from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.notification_webhook_broadcaster import NotificationWebhookBroadcaster

class TestIncidentNotificationBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_dir = tempfile.mkdtemp()
        self.dispatcher = NotificationChannelDispatcher()
        self.template_engine = NotificationTemplateEngine()
        self.severity_evaluator = IncidentSeverityEvaluator()
        self.webhook_broadcaster = NotificationWebhookBroadcaster()
        
        self.bridge = IncidentNotificationBridge(
            dispatcher=self.dispatcher,
            template_engine=self.template_engine,
            webhook_broadcaster=self.webhook_broadcaster,
            storage_dir=self.storage_dir,
            severity_evaluator=self.severity_evaluator
        )

    def tearDown(self):
        for root, dirs, files in os.walk(self.storage_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.storage_dir)

    def test_end_to_end_critical_incident_dispatch_and_evaluation(self):
        rand_id = str(uuid.uuid4())
        error_message = f"Critical system failure index {random.randint(1000, 9999)}"
        
        aggregated_incident = {
            "id": rand_id,
            "message": error_message,
            "traceboard_str": "Traceback (most recent call last):\n  File 'system.py', line 42, in run\n    raise SystemError()"
        }

        result = self.bridge.dispatch_critical_incident(aggregated_incident)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("incident_id"), rand_id)
        self.assertEqual(result.get("dispatch_id"), f"dispatch_{rand_id}")

        self.assertIn("severity_assessment", aggregated_incident)
        self.assertIsInstance(aggregated_incident["severity_assessment"], dict)

        expected_file_path = os.path.join(self.storage_dir, f"{rand_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            stored_data = json.load(f)
            self.assertEqual(stored_data.get("id"), rand_id)
            self.assertEqual(stored_data.get("message"), error_message)
            self.assertIn("severity_assessment", stored_data)

    def test_process_incident_deduplication_and_template_flow(self):
        incident_id = str(uuid.uuid4())
        payload = {
            "incident_id": incident_id,
            "service": f"auth-service-{random.randint(1, 100)}",
            "status": "DOWN"
        }

        first_processed = self.bridge.process_incident(payload)
        self.assertTrue(first_processed)

        second_processed = self.bridge.process_incident(payload)
        self.assertFalse(second_processed)

if __name__ == "__main__":
    unittest.main()