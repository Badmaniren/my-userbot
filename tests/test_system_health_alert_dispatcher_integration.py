import unittest
import uuid
import random
import os
import tempfile
from skills.system_health_alert_dispatcher import system_health_alert_dispatcher
from skills.system_health_aggregator import system_health_aggregator
from skills.system_health_telemetry_collector import system_health_telemetry_collector
from skills.incident_aggregator import incident_aggregator
from skills.notification_channel_dispatcher import notification_channel_dispatcher

class TestSystemHealthAlertDispatcherIntegration(unittest.TestCase):
    def test_alert_dispatcher_end_to_end_flow(self):
        random_node_id = str(uuid.uuid4())
        random_metric_value = round(random.uniform(85.0, 99.9), 2)
        random_error_code = f"ERR-{random.randint(1000, 9999)}"
        
        telemetry_data = system_health_telemetry_collector(
            node_id=random_node_id,
            cpu_usage=random_metric_value,
            error_code=random_error_code
        )
        
        aggregated_health = system_health_aggregator(
            telemetry_payload=telemetry_data
        )
        
        incident_payload = incident_aggregator(
            health_status=aggregated_health,
            severity="CRITICAL"
        )
        
        channel_config = notification_channel_dispatcher(
            target_service="pagerduty",
            routing_key=str(uuid.uuid4())
        )
        
        dispatch_result = system_health_alert_dispatcher(
            incident=incident_payload,
            channels=channel_config,
            verify_delivery=True
        )
        
        self.assertIsInstance(dispatch_result, dict)
        self.assertIn("dispatch_id", dispatch_result)
        self.assertEqual(dispatch_result.get("status"), "dispatched")
        self.assertEqual(dispatch_result.get("node_id"), random_node_id)
        
        if "log_file_path" in dispatch_result:
            self.assertTrue(os.path.exists(dispatch_result["log_file_path"]))
            with open(dispatch_result["log_file_path"], "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(random_node_id, content)
                self.assertIn(random_error_code, content)

if __name__ == "__main__":
    unittest.main()