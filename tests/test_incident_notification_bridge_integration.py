import unittest
import os
import json
import uuid
import random
import tempfile

from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.incident_aggregator import IncidentAggregator
from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.notification_template_engine import NotificationTemplateEngine
from skills.notification_webhook_broadcaster import NotificationWebhookBroadcaster


class TestIncidentNotificationBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = self.temp_dir.name

        self.aggregator = IncidentAggregator()
        self.severity_evaluator = IncidentSeverityEvaluator()
        self.dispatcher = NotificationChannelDispatcher()
        self.template_engine = NotificationTemplateEngine()
        self.webhook_broadcaster = NotificationWebhookBroadcaster()

        self.bridge = IncidentNotificationBridge(
            dispatcher=self.dispatcher,
            template_engine=self.template_engine,
            webhook_broadcaster=self.webhook_broadcaster,
            storage_dir=self.storage_dir
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_full_incident_notification_pipeline_integration(self):
        unique_incident_id = str(uuid.uuid4())
        random_error_code = random.randint(500, 599)
        random_service_name = f"service-{random.randint(1000, 9999)}"

        raw_incident = {
            "incident_id": unique_incident_id,
            "service": random_service_name,
            "error_code": random_error_code,
            "message": "Database connection timeout during heavy load."
        }

        aggregated_incident = self.aggregator.aggregate([raw_incident]) if hasattr(self.aggregator, "aggregate") else raw_incident
        if isinstance(aggregated_incident, list):
            aggregated_incident = aggregated_incident[0] if aggregated_incident else raw_incident

        severity_result = self.severity_evaluator.evaluate(aggregated_incident) if hasattr(self.severity_evaluator, "evaluate") else {"severity": "HIGH"}

        aggregated_incident["severity_assessment"] = severity_result

        dispatch_result = self.bridge.dispatch_critical_incident(aggregated_incident)

        self.assertIsInstance(dispatch_result, dict)
        self.assertEqual(dispatch_result.get("incident_id"), unique_incident_id)
        self.assertTrue(dispatch_result.get("success"))

        expected_file_path = os.path.join(self.storage_dir, f"{unique_incident_id}.json")
        self.assertTrue(os.path.exists(expected_file_path), "Integration failed: Storage did not persist the incident file.")

        with open(expected_file_path, 'r', encoding='utf-8') as f:
            persisted_data = json.load(f)

        self.assertEqual(persisted_data.get("incident_id"), unique_incident_id)
        self.assertEqual(persisted_data.get("error_code"), random_error_code)

        channel_name = f"channel-{random.randint(100, 999)}"
        template_name = "default"
        
        processing_success = self.bridge.process_incident(persisted_data, channel=channel_name, template=template_name)
        self.assertTrue(processing_success, "Integration failed: Bridge failed to process the unique incident.")

        duplicate_processing_success = self.bridge.process_incident(persisted_data, channel=channel_name, template=template_name)
        self.assertFalse(duplicate_processing_success, "Integration failed: Bridge processed duplicate incident ID.")

        webhook_url = f"https://webhook.internal.net/events/{uuid.uuid4()}"
        webhook_response = self.bridge.broadcast_to_webhooks(webhook_url, persisted_data)
        self.assertIsNotNone(webhook_response)


if __name__ == "__main__":
    unittest.main()