import unittest
from unittest.mock import patch
import uuid
import random

from skills.incident_sla_notification_dispatch import (
    dispatch_incident_sla_notification,
    incident_sla_notification_dispatch,
    IncidentSLANotificationDispatcher,
)

class TestIncidentSlaNotificationDispatch(unittest.TestCase):

    def test_dispatch_incident_sla_notification_randomized(self):
        inc_id = f"inc-{uuid.uuid4().hex[:8]}"
        threshold_val = random.randint(10, 100)
        recipient_addr = f"ops-{uuid.uuid4().hex[:6]}@example.com"
        channel_name = random.choice(["email", "slack", "pagerduty", "sms"])

        with patch("skills.incident_sla_notification_dispatch.incident_notification_broadcaster") as mock_broadcaster:
            mock_status = random.choice(["dispatched", "queued", "delivered"])
            mock_broadcaster.broadcast.return_value = {"status": mock_status}

            result = dispatch_incident_sla_notification(
                incident_id=inc_id,
                threshold=threshold_val,
                recipient=recipient_addr,
                channel=channel_name
            )

            mock_broadcaster.broadcast.assert_called_once_with(
                incident_id=inc_id,
                threshold=threshold_val,
                recipient=recipient_addr,
                channel=channel_name
            )

            self.assertEqual(result["incident_id"], inc_id)
            self.assertEqual(result["status"], mock_status)
            self.assertEqual(result["target"], recipient_addr)

    def test_incident_sla_notification_dispatch_payload_wrapping(self):
        inc_id = f"inc-{uuid.uuid4().hex[:8]}"
        custom_status = random.choice(["sent", "pending", "failed"])
        payload = {
            "incident_id": inc_id,
            "dispatch_reference": {
                "status": custom_status
            }
        }

        result = incident_sla_notification_dispatch(payload)

        self.assertIn("notification_id", result)
        self.assertEqual(result["incident_id"], inc_id)
        self.assertEqual(result["status"], custom_status)

    def test_incident_sla_notification_dispatcher_handle_sla_breach(self):
        dispatcher = IncidentSLANotificationDispatcher()
        inc_id = f"inc-{uuid.uuid4().hex[:8]}"
        severity_val = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        with patch("skills.incident_sla_notification_dispatch.notification_webhook_broadcaster") as mock_webhook:
            res = dispatcher.handle_sla_breach(incident_id=inc_id, severity=severity_val)
            self.assertTrue(res)
            mock_webhook.post.assert_called_once()

    def test_incident_sla_notification_dispatcher_render_template(self):
        dispatcher = IncidentSLANotificationDispatcher()
        template_name = f"tpl-{uuid.uuid4().hex[:6]}"
        msg_content = f"msg-{uuid.uuid4().hex}"
        context = {"msg": msg_content}

        with patch("skills.incident_sla_notification_dispatch.notification_template_engine") as mock_engine:
            mock_engine.render.return_value = f"rendered-{msg_content}"
            rendered = dispatcher.render_notification_template(template_name, context)

            mock_engine.render.assert_called_once_with(template_name, context)
            self.assertIn(msg_content, rendered)

    def test_incident_sla_notification_dispatcher_verify_and_dispatch(self):
        dispatcher = IncidentSLANotificationDispatcher()
        inc_id = f"inc-{uuid.uuid4().hex[:8]}"

        with patch("skills.incident_sla_notification_dispatch.incident_sla_tracker") as mock_tracker, \
             patch("skills.incident_sla_notification_dispatch.dispatch_incident_sla_notification") as mock_dispatch:

            mock_dispatch.return_value = {
                "incident_id": inc_id,
                "status": "dispatched",
                "target": "default-ops@example.com"
            }

            res = dispatcher.verify_and_dispatch(incident_id=inc_id)

            mock_tracker.check_status.assert_called_once_with({"incident_id": inc_id, "action": "verify"})
            mock_dispatch.assert_called_once()
            self.assertEqual(res["incident_id"], inc_id)


if __name__ == "__main__":
    unittest.main()