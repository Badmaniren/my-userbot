import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import random
import uuid

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla


class TestIncidentSLATracker(unittest.TestCase):
    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.sla_thresholds = {
            "LOW": random.randint(7200, 10800),
            "MEDIUM": random.randint(3600, 7199),
            "HIGH": random.randint(1800, 3599),
            "CRITICAL": random.randint(300, 1799)
        }
        self.warning_threshold_pct = round(random.uniform(0.7, 0.9), 2)
        self.tracker = IncidentSLATracker(self.sla_thresholds, self.warning_threshold_pct)

    def test_register_incident(self):
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        self.assertIn(self.incident_id, self.tracker.incidents)
        incident = self.tracker.incidents[self.incident_id]
        self.assertEqual(incident["severity"], self.severity)
        self.assertEqual(incident["created_at"], created_at)
        self.assertEqual(incident["status"], "ACTIVE")

    def test_get_time_to_breach_success(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        current_time = created_at + timedelta(seconds=random.randint(10, 500))
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id, current_time)

        expected_limit = self.sla_thresholds[self.severity]
        elapsed = (current_time - created_at).total_seconds()
        expected_remaining = float(expected_limit - elapsed)

        self.assertEqual(time_to_breach, expected_remaining)

    def test_get_time_to_breach_not_found(self):
        missing_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(missing_id)

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
        warning_time_offset = int(sla_limit * self.warning_threshold_pct) + random.randint(1, 10)
        current_time = created_at + timedelta(seconds=warning_time_offset)

        results = self.tracker.check_sla_breaches(current_time=current_time)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["incident_id"], self.incident_id)
        self.assertEqual(results[0]["status"], "WARNING")

    def test_check_sla_breaches_breached_with_hooks(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        sla_limit = self.sla_thresholds[self.severity]
        breach_time_offset = sla_limit + random.randint(10, 100)
        current_time = created_at + timedelta(seconds=breach_time_offset)

        mock_notification_bridge = MagicMock()
        mock_escalation_engine = MagicMock()

        results = self.tracker.check_sla_breaches(
            current_time=current_time,
            notification_bridge=mock_notification_bridge,
            escalation_engine=mock_escalation_engine
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["incident_id"], self.incident_id)
        self.assertEqual(results[0]["status"], "BREACHED")

        mock_notification_bridge.notify_sla_breach.assert_called_once_with(
            incident_id=self.incident_id, severity=self.severity
        )
        mock_escalation_engine.escalate_incident.assert_called_once_with(
            incident_id=self.incident_id, severity=self.severity
        )

    def test_check_sla_breaches_ignores_resolved(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        self.tracker.update_incident_status(self.incident_id, "RESOLVED")

        sla_limit = self.sla_thresholds[self.severity]
        current_time = created_at + timedelta(seconds=sla_limit + 500)

        results = self.tracker.check_sla_breaches(current_time=current_time)
        self.assertEqual(len(results), 0)

    def test_track_incident_sla_function(self):
        timestamp = int(datetime.now().timestamp()) - random.randint(100, 1000)
        threshold = random.randint(1800, 7200)

        sla_input = {
            "incident_id": self.incident_id,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp
                }
            },
            "threshold_seconds": threshold
        }

        result = track_incident_sla(sla_input)

        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIsInstance(result["breach_predicted"], bool)
        self.assertIsInstance(result["time_remaining_seconds"], float)


if __name__ == "__main__":
    unittest.main()