import unittest
import os
import json
import uuid
import random
import tempfile
from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.incident_aggregator import IncidentAggregator
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.notification_template_engine import NotificationTemplateEngine

class TestIncidentNotificationBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.aggregator = IncidentAggregator()
        self.dispatcher = NotificationChannelDispatcher()
        self.template_engine = NotificationTemplateEngine()
        
        self.bridge = IncidentNotificationBridge(
            dispatcher=self.dispatcher,
            template_engine=self.template_engine,
            storage_dir=self.temp_dir.name
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_end_to_end_incident_processing_and_storage(self):
        random_id = f"inc_{uuid.uuid4().hex}"
        severity_levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        selected_severity = random.choice(severity_levels)
        
        raw_incident = {
            "incident_id": random_id,
            "severity": selected_severity,
            "description": f"Integration test security event {random.randint(1000, 9999)}",
            "source": "vulnerability_scanner"
        }

        aggregated_data = self.aggregator.aggregate([raw_incident]) if hasattr(self.aggregator, "aggregate") else raw_incident
        if isinstance(aggregated_data, list) and len(aggregated_data) > 0:
            incident_payload = aggregated_data[0]
        else:
            incident_payload = raw_incident

        incident_payload["incident_id"] = random_id

        dispatch_result = self.bridge.dispatch_critical_incident(incident_payload)
        
        self.assertEqual(dispatch_result.get("incident_id"), random_id)
        self.assertTrue(dispatch_result.get("success"))

        expected_file_path = os.path.join(self.temp_dir.name, f"{random_id}.json")
        self.assertTrue(os.path.exists(expected_file_path), "Файл критического инцидента не был создан в storage_dir")

        with open(expected_file_path, 'r', encoding='utf-8') as f:
            stored_data = json.load(f)
        self.assertEqual(stored_data.get("incident_id"), random_id)
        self.assertEqual(stored_data.get("severity"), selected_severity)

        processed_first = self.bridge.process_incident(incident_payload, channel="default_channel")
        self.assertTrue(processed_first)

        processed_duplicate = self.bridge.process_incident(incident_payload, channel="default_channel")
        self.assertFalse(processed_duplicate, "Дубликат инцидента должен быть отклонен мостом")

if __name__ == "__main__":
    unittest.main()