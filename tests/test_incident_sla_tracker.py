import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid
import random

from skills.incident_sla_tracker import (
    IncidentSLATracker,
    track_incident_sla
)


class TestIncidentSLATracker(unittest.TestCase):

    def setUp(self):
        self.incident_id = str(uuid.uuid4())
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.thresholds = {
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 900
        }
        self.warning_pct = 0.8
        self.tracker = IncidentSLATracker(
            sla_thresholds=self.thresholds,
            warning_threshold_pct=self.warning_pct
        )

    def test_register_incident_and_time_to_breach(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        self.assertIn(self.incident_id, self.tracker.incidents)
        incident = self.tracker.incidents[self.incident_id]
        self.assertEqual(incident["severity"], self.severity)
        self.assertEqual(incident["status"], "ACTIVE")

        future_time = created_at + timedelta(seconds=100)
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id, current_time=future_time)
        expected_limit = self.thresholds[self.severity]
        self.assertEqual(time_to_breach, expected_limit - 100)

    def test_get_time_to_breach_nonexistent_raises_key_error(self):
        fake_id = str(uuid.uuid4())
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(fake_id)

    def test_update_incident_status(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"
        self.tracker.update_incident_status(self.incident_id, new_status)
        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], new_status)

    def test_check_sla_breaches_warning_and_breach(self):
        created_at = datetime.now()
        limit = self.thresholds[self.severity]

        incident_warning_id = str(uuid.uuid4())
        incident_breach_id = str(uuid.uuid4())
        incident_resolved_id = str(uuid.uuid4())

        self.tracker.register_incident(incident_warning_id, self.severity, created_at)
        self.tracker.register_incident(incident_breach_id, self.severity, created_at)
        self.tracker.register_incident(incident_resolved_id, self.severity, created_at)
        self.tracker.update_incident_status(incident_resolved_id, "RESOLVED")

        warning_time = created_at + timedelta(seconds=int(limit * self.warning_pct))
        breach_time = created_at + timedelta(seconds=limit + 50)

        mock_notification = MagicMock()
        mock_escalation = MagicMock()

        results = self.tracker.check_sla_breaches(
            current_time=warning_time,
            notification_bridge=mock_notification,
            escalation_engine=mock_escalation
        )

        warning_found = any(r["incident_id"] == incident_warning_id and r["status"] == "WARNING" for r in results)
        self.assertTrue(warning_found)

        results_breach = self.tracker.check_sla_breaches(
            current_time=breach_time,
            notification_bridge=mock_notification,
            escalation_engine=mock_escalation
        )

        breach_found = any(r["incident_id"] == incident_breach_id and r["status"] == "BREACHED" for r in results_breach)
        self.assertTrue(breach_found)
        mock_notification.notify_sla_breach.assert_called()
        mock_escalation.escalate_incident.assert_called()

        resolved_found = any(r["incident_id"] == incident_resolved_id for r in results_breach)
        self.assertFalse(resolved_found)

    def test_track_incident_sla_function_with_timestamp(self):
        timestamp = int(datetime.now().timestamp()) - 500
        threshold = random.randint(1000, 5000)
        sla_input = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp
                }
            }
        }

        with patch("skills.incident_sla_tracker.evaluate_incident_severity") as mock_eval:
            result = track_incident_sla(sla_input)

            self.assertEqual(result["incident_id"], self.incident_id)
            self.assertIn("breach_predicted", result)
            self.assertIn("time_remaining_seconds", result)
            mock_eval.assert_called()

    def test_track_incident_sla_function_fallback_signature(self):
        sla_input = {
            "incident_id": self.incident_id,
            "threshold_seconds": random.randint(100, 500),
            "aggregated_data": {}
        }

        with patch("skills.incident_sla_tracker.evaluate_incident_severity") as mock_eval:
            mock_eval.side_effect = TypeError("missing required arguments")
            
            result = track_incident_sla(sla_input)
            
            self.assertEqual(result["incident_id"], self.incident_id)
            self.assertEqual(mock_eval.call_count, 1)