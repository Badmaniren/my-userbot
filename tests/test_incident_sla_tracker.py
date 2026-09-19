import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid
import random

from skills.incident_sla_tracker import (
    IncidentSLATracker,
    track_incident_sla,
)

class TestIncidentSLATracker(unittest.TestCase):
    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"])
        self.created_at = datetime.now() - timedelta(seconds=random.randint(10, 500))
        self.sla_thresholds = {
            self.severity: random.randint(600, 3600)
        }
        self.warning_threshold_pct = 0.8
        self.tracker = IncidentSLATracker(
            sla_thresholds=self.sla_thresholds,
            warning_threshold_pct=self.warning_threshold_pct
        )

    def test_register_incident_and_time_to_breach(self):
        self.tracker.register_incident(
            incident_id=self.incident_id,
            severity=self.severity,
            created_at=self.created_at
        )
        self.assertIn(self.incident_id, self.tracker.incidents)

        current_time = self.created_at + timedelta(seconds=100)
        time_to_breach = self.tracker.get_time_to_breach(
            incident_id=self.incident_id,
            current_time=current_time
        )
        expected = float(self.sla_thresholds[self.severity] - 100)
        self.assertEqual(time_to_breach, expected)

    def test_get_time_to_breach_key_error(self):
        missing_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(incident_id=missing_id)

    def test_update_incident_status(self):
        self.tracker.register_incident(
            incident_id=self.incident_id,
            severity=self.severity,
            created_at=self.created_at
        )
        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"
        self.tracker.update_incident_status(
            incident_id=self.incident_id,
            status=new_status
        )
        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], new_status)

    def test_check_sla_breaches_warning_and_breach(self):
        warning_time = self.created_at + timedelta(seconds=int(self.sla_thresholds[self.severity] * 0.85))
        breach_time = self.created_at + timedelta(seconds=self.sla_thresholds[self.severity] + 50)

        incident_warning = uuid.uuid4().hex
        incident_breach = uuid.uuid4().hex

        self.tracker.register_incident(incident_id=incident_warning, severity=self.severity, created_at=self.created_at)
        self.tracker.register_incident(incident_id=incident_breach, severity=self.severity, created_at=self.created_at)

        mock_bridge = MagicMock()
        mock_escalation = MagicMock()

        with patch("skills.incident_sla_tracker.datetime") as mock_datetime:
            mock_datetime.now.return_value = breach_time
            results = self.tracker.check_sla_breaches(
                current_time=breach_time,
                notification_bridge=mock_bridge,
                escalation_engine=mock_escalation
            )

        self.assertTrue(any(r["incident_id"] == incident_breach and r["status"] == "BREACHED" for r in results))
        mock_bridge.notify_sla_breach.assert_called()
        mock_escalation.escalate_incident.assert_called()

    def test_track_incident_sla_utility(self):
        timestamp = int(datetime.now().timestamp()) - random.randint(100, 1000)
        threshold = random.randint(2000, 5000)
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
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)
        self.assertIsInstance(result["time_remaining_seconds"], float)

if __name__ == "__main__":
    unittest.main()