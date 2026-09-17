import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid
import random
import string

from skills.incident_sla_tracker import (
    IncidentSLATracker,
    track_incident_sla,
    incident_notification_bridge,
    incident_auto_escalation_engine
)


class TestIncidentSLATracker(unittest.TestCase):
    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.sla_thresholds = {
            "LOW": random.randint(7200, 14400),
            "MEDIUM": random.randint(3600, 7199),
            "HIGH": random.randint(1800, 3599),
            "CRITICAL": random.randint(300, 1799)
        }
        self.warning_threshold_pct = random.uniform(0.5, 0.8)
        self.tracker = IncidentSLATracker(
            sla_thresholds=self.sla_thresholds,
            warning_threshold_pct=self.warning_threshold_pct
        )

    def test_register_incident_and_time_to_breach(self):
        created_at = datetime.now() - timedelta(seconds=100)
        self.tracker.register_incident(
            incident_id=self.incident_id,
            severity=self.severity,
            created_at=created_at
        )
        
        self.assertIn(self.incident_id, self.tracker.incidents)
        self.assertEqual(self.tracker.incidents[self.incident_id]["severity"], self.severity)
        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], "ACTIVE")

        current_time = datetime.now()
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id, current_time=current_time)

        expected_limit = self.sla_thresholds[self.severity]
        elapsed = (current_time - created_at).total_seconds()
        expected_ttl = float(expected_limit - elapsed)
        
        self.assertAlmostEqual(time_to_breach, expected_ttl, delta=1.0)

    def test_get_time_to_breach_not_found(self):
        non_existent_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(non_existent_id)

    def test_update_incident_status(self):
        created_at = datetime.now()
        self.tracker.register_incident(
            incident_id=self.incident_id,
            severity=self.severity,
            created_at=created_at
        )
        
        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"
        self.tracker.update_incident_status(self.incident_id, status=new_status)
        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], new_status)

    def test_check_sla_breaches_warning_and_breached(self):
        warning_severity = list(self.sla_thresholds.keys())[0]
        limit = self.sla_thresholds[warning_severity]
        
        warning_id = uuid.uuid4().hex
        breached_id = uuid.uuid4().hex
        resolved_id = uuid.uuid4().hex

        now = datetime.now()

        warning_elapsed = int(limit * self.warning_threshold_pct) + 10
        breached_elapsed = limit + 50
        
        self.tracker.register_incident(warning_id, warning_severity, now - timedelta(seconds=warning_elapsed))
        self.tracker.register_incident(breached_id, warning_severity, now - timedelta(seconds=breached_elapsed))
        self.tracker.register_incident(resolved_id, warning_severity, now - timedelta(seconds=breached_elapsed))
        self.tracker.update_incident_status(resolved_id, "RESOLVED")

        mock_notification = MagicMock()
        mock_escalation = MagicMock()

        results = self.tracker.check_sla_breaches(
            current_time=now,
            notification_bridge=mock_notification,
            escalation_engine=mock_escalation
        )

        result_statuses = {res["incident_id"]: res["status"] for res in results}
        
        self.assertIn(warning_id, result_statuses)
        self.assertEqual(result_statuses[warning_id], "WARNING")
        
        self.assertIn(breached_id, result_statuses)
        self.assertEqual(result_statuses[breached_id], "BREACHED")
        
        self.assertNotIn(resolved_id, result_statuses)

        mock_notification.notify_sla_breach.assert_called_once_with(incident_id=breached_id, severity=warning_severity)
        mock_escalation.escalate_incident.assert_called_once_with(incident_id=breached_id, severity=warning_severity)

    def test_track_incident_sla_function(self):
        threshold = random.randint(1000, 5000)
        timestamp = int(datetime.now().timestamp()) - 500
        
        sla_input = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp
                }
            }
        }
        
        result = track_incident_sla(sla_input)
        
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)
        self.assertIsInstance(result["breach_predicted"], bool)
        self.assertIsInstance(result["time_remaining_seconds"], float)

    def test_module_level_mocks_exist(self):
        self.assertTrue(hasattr(sys_mod := __import__("skills.incident_sla_tracker", fromlist=["incident_notification_bridge"]), "incident_notification_bridge"))
        self.assertTrue(hasattr(sys_mod, "incident_auto_escalation_engine"))


if __name__ == "__main__":
    unittest.main()