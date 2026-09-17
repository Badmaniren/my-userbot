import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid
import random
import string

from skills.incident_sla_tracker import (
    IncidentSLATracker,
    IncidentSlaTracker,
    track_incident_sla,
    get_tracking_data,
    get_active_tracker,
    get_tracker_details,
    incident_sla_tracker
)


class TestIncidentSLATracker(unittest.TestCase):

    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.sla_thresholds = {
            "LOW": random.randint(7200, 14400),
            "MEDIUM": random.randint(3600, 7199),
            "HIGH": random.randint(1800, 3599),
            "CRITICAL": random.randint(60, 1799)
        }
        self.warning_threshold_pct = round(random.uniform(0.5, 0.9), 2)

        self.tracker = IncidentSLATracker(
            sla_thresholds=self.sla_thresholds,
            warning_threshold_pct=self.warning_threshold_pct
        )

    def test_register_incident(self):
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        self.assertIn(self.incident_id, self.tracker.incidents)
        incident_data = self.tracker.incidents[self.incident_id]
        self.assertEqual(incident_data["severity"], self.severity)
        self.assertEqual(incident_data["created_at"], created_at)
        self.assertEqual(incident_data["status"], "ACTIVE")

    def test_get_time_to_breach_success(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        current_time = created_at + timedelta(seconds=15)
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id, current_time)

        expected_limit = self.sla_thresholds[self.severity]
        self.assertEqual(time_to_breach, float(expected_limit - 15))

    def test_get_time_to_breach_not_found(self):
        non_existent_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(non_existent_id)

    def test_update_incident_status(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        new_status = f"RESOLVED_{uuid.uuid4().hex[:6].upper()}"
        self.tracker.update_incident_status(self.incident_id, new_status)

        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], new_status)

    def test_check_sla_breaches_warning(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        sla_limit = self.sla_thresholds[self.severity]
        elapsed_time = int(sla_limit * self.warning_threshold_pct) + 5
        current_time = created_at + timedelta(seconds=elapsed_time)

        results = self.tracker.check_sla_breaches(current_time=current_time)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["incident_id"], self.incident_id)
        self.assertEqual(results[0]["status"], "WARNING")

    def test_check_sla_breaches_breached_with_hooks(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        sla_limit = self.sla_thresholds[self.severity]
        elapsed_time = sla_limit + random.randint(10, 100)
        current_time = created_at + timedelta(seconds=elapsed_time)

        mock_bridge = MagicMock()
        mock_escalation = MagicMock()

        results = self.tracker.check_sla_breaches(
            current_time=current_time,
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["incident_id"], self.incident_id)
        self.assertEqual(results[0]["status"], "BREACHED")

        mock_bridge.notify_sla_breach.assert_called_once_with(
            incident_id=self.incident_id,
            severity=self.severity
        )
        mock_escalation.escalate_incident.assert_called_once_with(
            incident_id=self.incident_id,
            severity=self.severity
        )

    def test_check_sla_breaches_resolved_ignored(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        self.tracker.update_incident_status(self.incident_id, "RESOLVED_SUCCESS")

        sla_limit = self.sla_thresholds[self.severity]
        current_time = created_at + timedelta(seconds=sla_limit + 500)

        results = self.tracker.check_sla_breaches(current_time=current_time)
        self.assertEqual(len(results), 0)

    def test_track_incident_sla_function(self):
        timestamp = int(datetime.now().timestamp()) - random.randint(50, 200)
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

        result = track_incident_sla(sla_input)

        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)
        self.assertIsInstance(result["breach_predicted"], bool)
        self.assertIsInstance(result["time_remaining_seconds"], float)

    def test_additional_helper_methods_and_functions(self):
        self.assertEqual(IncidentSlaTracker, IncidentSLATracker)
        
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        metrics = self.tracker.get_incident_sla_metrics(self.incident_id)
        self.assertEqual(metrics["incident_id"], self.incident_id)
        self.assertEqual(metrics["severity"], self.severity)

        track_res = self.tracker.track({"incident_id": self.incident_id, "severity": self.severity})
        self.assertIn("incident_id", track_res)

        tracking_data = get_tracking_data(self.incident_id)
        self.assertIn("incident_id", tracking_data)

        active = get_active_tracker(self.incident_id)
        self.assertIn("tracker_id", active)

        details = get_tracker_details(self.incident_id)
        self.assertIn("tracker_id", details)

        wrapper_res = incident_sla_tracker({"incident_id": self.incident_id})
        self.assertIn("incident_id", wrapper_res)


if __name__ == "__main__":
    unittest.main()