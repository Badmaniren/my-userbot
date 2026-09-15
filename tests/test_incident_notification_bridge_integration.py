import unittest
import uuid
import random
import os
import tempfile
from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.incident_aggregator import IncidentAggregator
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.notification_template_engine import NotificationTemplateEngine

class TestIncidentNotificationBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.bridge = IncidentNotificationBridge(storage_dir=self.temp_dir.name)
        self.aggregator = IncidentAggregator()
        self.dispatcher = NotificationChannelDispatcher()
        self.template_engine = NotificationTemplateEngine()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_incident_to_notification_flow(self):
        unique_incident_id = str(uuid.uuid4())
        random_error_code = random.randint(1000, 9999)
        severity_levels = ["CRITICAL", "HIGH", "EMERGENCY"]
        chosen_severity = random.choice(severity_levels)
        
        incident_data = {
            "id": unique_incident_id,
            "code": random_error_code,
            "severity": chosen_severity,
            "source": "security_scanner",
            "message": f"Integration test critical security event {unique_incident_id}"
        }

        aggregated_incident = self.aggregator.process_raw_incident(incident_data)
        self.assertIsNotNone(aggregated_incident)
        
        bridge_result = self.bridge.dispatch_critical_incident(aggregated_incident)
        
        self.assertIn("dispatch_id", bridge_result)
        self.assertEqual(bridge_result["incident_id"], unique_incident_id)
        self.assertTrue(bridge_result["success"])

        expected_file_path = os.path.join(self.temp_dir.name, f"{unique_incident_id}.json")
        self.assertTrue(os.path.exists(expected_file_path), "Интеграционный модуль должен сохранять артефакт инцидента на диск")

        rendered_template = self.template_engine.render("security_alert", {
            "incident_id": unique_incident_id,
            "error_code": random_error_code,
            "severity": chosen_severity
        })
        self.assertIn(unique_incident_id, rendered_template)
        self.assertIn(str(random_error_code), rendered_template)

if __name__ == "__main__":
    unittest.main()