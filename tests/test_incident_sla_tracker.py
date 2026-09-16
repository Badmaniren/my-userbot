import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid
import random

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla

class TestIncidentSLATracker(unittest.TestCase):
    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"])
        self.warning_threshold_pct = random.uniform(0.5, 0.9)
        self.thresholds = {self.severity: random.randint(1000, 7200)}
        self.tracker = IncidentSLATracker(self.thresholds, self.warning_threshold_pct)

    def test_register_and_get_time_to_breach(self):
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id)
        self.assertIsInstance(time_to_breach, float)

    def test_get_time_to_breach_not_found(self):
        missing_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(missing_id)

    def test_update_incident_status(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"
        self.tracker.update_incident_status(self.incident_id, new_status)
        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], new_status)

    def test_check_sla_breaches_warning_and_breach(self):
        limit = self.thresholds[self.severity]
        created_at_warning = datetime.now() - timedelta(seconds=int(limit * self.warning_threshold_pct) + 5)
        id_warning = uuid.uuid4().hex
        
        created_at_breach = datetime.now() - timedelta(seconds=limit + 50)
        id_breach = uuid.uuid4().hex

        self.tracker.register_incident(id_warning, self.severity, created_at_warning)
        self.tracker.register_incident(id_breach, self.severity, created_at_breach)

        mock_bridge = MagicMock()
        mock_escalation = MagicMock()

        results = self.tracker.check_sla_breaches(
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )

        self.assertIsInstance(results, list)
        found_statuses = {res["incident_id"]: res["status"] for res in results}
        self.assertIn(id_warning, found_statuses)
        self.assertEqual(found_statuses[id_warning], "WARNING")
        self.assertIn(id_breach, found_statuses)
        self.assertEqual(found_statuses[id_breach], "BREACHED")
        mock_bridge.notify_sla_breach.assert_called()
        mock_escalation.escalate_incident.assert_called()

    def test_track_incident_sla_function(self):
        timestamp = int(datetime.now().timestamp()) - random.randint(10, 500)
        threshold = random.randint(1000, 5000)
        payload = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp
                }
            }
        }
        res = track_incident_sla(payload)
        self.assertEqual(res["incident_id"], self.incident_id)
        self.assertIn("breach_predicted", res)
        self.assertIn("time_remaining_seconds", res)

    def test_track_incident_sla_no_timestamp(self):
        threshold = random.randint(1000, 5000)
        payload = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {}
        }
        res = track_incident_sla(payload)
        self.assertEqual(res["incident_id"], self.incident_id)
        self.assertIsInstance(res["breach_predicted"], bool)
        self.assertIsInstance(res["time_remaining_seconds"], float)

if __name__ == "__main__":
    unittest.main()