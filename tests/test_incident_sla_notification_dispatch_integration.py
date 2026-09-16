import unittest
import uuid
import random

from skills.incident_sla_notification_dispatch import (
    IncidentSLANotificationDispatcher,
    dispatch_incident_sla_notification,
    incident_sla_notification_dispatch
)
from skills.incident_sla_tracker import incident_sla_tracker

class TestIncidentSLANotificationDispatchIntegration(unittest.TestCase):

    def test_end_to_end_sla_notification_dispatch(self):
        unique_incident_id = f"inc-{uuid.uuid4().hex}"
        random_threshold = random.randint(10, 60)
        random_recipient = f"ops-{uuid.uuid4().hex[:8]}@example.com"
        random_channel = random.choice(["email", "slack", "sms", "webhook"])

        dispatch_result = dispatch_incident_sla_notification(
            incident_id=unique_incident_id,
            threshold=random_threshold,
            recipient=random_recipient,
            channel=random_channel
        )

        self.assertIsInstance(dispatch_result, dict)
        self.assertEqual(dispatch_result.get("incident_id"), unique_incident_id)
        self.assertEqual(dispatch_result.get("target"), random_recipient)
        self.assertIn("status", dispatch_result)

        payload_wrapper = {
            "incident_id": unique_incident_id,
            "dispatch_reference": dispatch_result
        }
        wrapped_result = incident_sla_notification_dispatch(payload_wrapper)

        self.assertIsInstance(wrapped_result, dict)
        self.assertEqual(wrapped_result.get("incident_id"), unique_incident_id)
        self.assertIn("notification_id", wrapped_result)
        self.assertIsInstance(wrapped_result.get("notification_id"), str)
        self.assertTrue(len(wrapped_result.get("notification_id")) > 0)

        dispatcher = IncidentSLANotificationDispatcher()
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        breach_handled = dispatcher.handle_sla_breach(unique_incident_id, random_severity)
        self.assertTrue(breach_handled)

        rendered_text = dispatcher.render_notification_template(
            "sla_alert_template",
            {"msg": f"Alert for {unique_incident_id}", "severity": random_severity}
        )
        self.assertIsInstance(rendered_text, str)

        verification_result = dispatcher.verify_and_dispatch(unique_incident_id)
        self.assertIsInstance(verification_result, dict)
        self.assertEqual(verification_result.get("incident_id"), unique_incident_id)
        self.assertEqual(verification_result.get("status"), "dispatched")

if __name__ == "__main__":
    unittest.main()