import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
import random
import uuid

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla

class TestIncidentSLATracker(unittest.TestCase):

    def setUp(self):
        self.severity_levels = [uuid.uuid4().hex for _ in range(3)]
        self.sla_thresholds = {
            self.severity_levels[0]: random.randint(300, 1000),
            self.severity_levels[1]: random.randint(1001, 2000),
            self.severity_levels[2]: random.randint(2001, 5000),
        }
        self.warning_pct = round(random.uniform(0.5, 0.9), 2)
        self.tracker = IncidentSLATracker(self.sla_thresholds, self.warning_pct)

    def test_register_incident_success(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(self.severity_levels)
        created_at = datetime.now(timezone.utc)

        self.tracker.register_incident(incident_id, severity, created_at)

        self.assertIn(incident_id, self.tracker.incidents)
        self.assertEqual(self.tracker.incidents[incident_id]["severity"], severity)
        self.assertEqual(self.tracker.incidents[incident_id]["created_at"], created_at)
        self.assertEqual(self.tracker.incidents[incident_id]["status"], "ACTIVE")

    def test_get_time_to_breach_active(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(self.severity_levels)
        sla_limit = self.sla_thresholds[severity]
        
        created_at = datetime.now(timezone.utc)
        self.tracker.register_incident(incident_id, severity, created_at)

        check_time = created_at + timedelta(seconds=100)
        time_to_breach = self.tracker.get_time_to_breach(incident_id, current_time=check_time)

        expected = float(sla_limit - 100)
        self.assertEqual(time_to_breach, expected)

    def test_get_time_to_breach_not_found(self):
        fake_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(fake_id)

    def test_update_incident_status(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(self.severity_levels)
        created_at = datetime.now(timezone.utc)
        
        self.tracker.register_incident(incident_id, severity, created_at)
        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"
        
        self.tracker.update_incident_status(incident_id, new_status)
        self.assertEqual(self.tracker.incidents[incident_id]["status"], new_status)

    def test_check_sla_breaches_warning_and_breach(self):
        severity = self.severity_levels[0]
        sla_limit = self.sla_thresholds[severity]

        id_warning = uuid.uuid4().hex
        id_breach = uuid.uuid4().hex
        id_normal = uuid.uuid4().hex

        now = datetime.now(timezone.utc)

        self.tracker.register_incident(id_warning, severity, now - timedelta(seconds=int(sla_limit * self.warning_pct)))
        self.tracker.register_incident(id_breach, severity, now - timedelta(seconds=sla_limit + 10))
        self.tracker.register_incident(id_normal, severity, now)

        mock_bridge = MagicMock()
        mock_escalation = MagicMock()

        results = self.tracker.check_sla_breaches(
            current_time=now,
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )

        statuses = {res["incident_id"]: res["status"] for res in results}

        self.assertEqual(statuses.get(id_warning), "WARNING")
        self.assertEqual(statuses.get(id_breach), "BREACHED")
        self.assertNotIn(id_normal, statuses)

        mock_bridge.notify_sla_breach.assert_called_once_with(incident_id=id_breach, severity=severity)
        mock_escalation.escalate_incident.assert_called_once_with(incident_id=id_breach, severity=severity)

    def test_check_sla_breaches_ignores_resolved(self):
        severity = self.severity_levels[0]
        sla_limit = self.sla_thresholds[severity]
        
        incident_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc)
        
        self.tracker.register_incident(incident_id, severity, now - timedelta(seconds=sla_limit + 100))
        self.tracker.update_incident_status(incident_id, "RESOLVED_MANUAL")

        results = self.tracker.check_sla_breaches(current_time=now)
        self.assertEqual(len(results), 0)

    def test_track_incident_sla_function(self):
        incident_id = uuid.uuid4().hex
        threshold = random.randint(500, 1500)
        timestamp = int(datetime.now(timezone.utc).timestamp()) - 200

        payload = {
            "incident_id": incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp
                }
            }
        }

        result = track_incident_sla(payload)

        self.assertEqual(result["incident_id"], incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)
        self.assertIsInstance(result["time_remaining_seconds"], float)

    def test_track_incident_sla_fallback_timestamp(self):
        incident_id = uuid.uuid4().hex
        threshold = random.randint(500, 1500)

        payload = {
            "incident_id": incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {}
        }

        result = track_incident_sla(payload)

        self.assertEqual(result["incident_id"], incident_id)
        self.assertIsInstance(result["time_remaining_seconds"], float)

if __name__ == "__main__":
    unittest.main()