import unittest
import uuid
import random
import os
import tempfile
from skills.incident_auto_escalation_engine import auto_escalate_incident
from skills.incident_aggregator import aggregate_incidents
from skills.incident_notification_bridge import bridge_incident_notification
from skills.incident_severity_evaluator import evaluate_incident_severity
from skills.incident_notification_broadcaster import broadcast_incident_notification
from skills.notification_channel_dispatcher import dispatch_notification_channel
from skills.notification_template_engine import render_notification_template
from skills.system_health_aggregator import aggregate_system_health

class TestIncidentAutoEscalationIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.incident_id = str(uuid.uuid4())
        self.source_system = f"system-{random.randint(1000, 9999)}"
        self.error_code = random.choice([500, 502, 503, 504, 404])
        self.metric_value = random.uniform(85.0, 99.9)

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_end_to_end_auto_escalation_integration(self):
        raw_payload = {
            "incident_id": self.incident_id,
            "source": self.source_system,
            "error_code": self.error_code,
            "cpu_load": self.metric_value,
            "timestamp": uuid.uuid4().hex
        }

        health_data = aggregate_system_health(
            metric_source=self.source_system,
            threshold=self.metric_value
        )
        self.assertIsNotNone(health_data)

        aggregated_incident = aggregate_incidents(
            incident_data=raw_payload,
            storage_path=self.test_dir
        )
        self.assertIn("incident_id", aggregated_incident)
        self.assertEqual(aggregated_incident["incident_id"], self.incident_id)

        severity_level = evaluate_incident_severity(
            incident_payload=aggregated_incident
        )
        self.assertIsNotNone(severity_level)

        rendered_template = render_notification_template(
            template_name="escalation_alert",
            context={"incident_id": self.incident_id, "severity": severity_level}
        )
        self.assertIsNotNone(rendered_template)

        bridged_notification = bridge_incident_notification(
            notification_content=rendered_template,
            target_channel="auto_escalation_channel"
        )
        self.assertIsNotNone(bridged_notification)

        dispatch_result = dispatch_notification_channel(
            channel_payload=bridged_notification,
            dispatch_mode="immediate"
        )
        self.assertTrue(dispatch_result)

        broadcast_result = broadcast_incident_notification(
            notification_id=str(uuid.uuid4()),
            payload=bridged_notification
        )
        self.assertTrue(broadcast_result)

        escalation_result = auto_escalate_incident(
            incident_id=self.incident_id,
            severity=severity_level,
            workspace_dir=self.test_dir
        )

        self.assertIsInstance(escalation_result, dict)
        self.assertEqual(escalation_result.get("escalated_incident_id"), self.incident_id)
        self.assertEqual(escalation_result.get("status"), "SUCCESS")

        expected_file_path = os.path.join(self.test_dir, f"escalated_{self.incident_id}.json")
        self.assertTrue(os.path.exists(expected_file_path), "Integration failed: Escalation audit file was not created on disk.")

if __name__ == "__main__":
    unittest.main()