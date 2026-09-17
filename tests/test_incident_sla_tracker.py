import unittest
from unittest.mock import MagicMock, patch
import random
import uuid
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla

class TestIncidentSLATracker(unittest.TestCase):
    def setUp(self):
        self.severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        self.random_severity = random.choice(self.severities)
        self.random_threshold = random.randint(1000, 5000)
        self.sla_thresholds = {self.random_severity: self.random_threshold}
        self.warning_pct = random.uniform(0.5, 0.8)
        self.tracker = IncidentSLATracker(self.sla_thresholds, self.warning_pct)

    def test_register_and_get_time_to_breach(self):
        incident_id = f"INC-{uuid.uuid4().hex[:8]}"
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))
        
        self.tracker.register_incident(incident_id, self.random_severity, created_at)
        
        current_time = created_at + timedelta(seconds=100)
        expected_remaining = float(self.random_threshold - 100)
        
        remaining = self.tracker.get_time_to_breach(incident_id, current_time)
        self.assertEqual(remaining, expected_remaining)

    def test_get_time_to_breach_missing_incident(self):
        fake_id = f"INC-{uuid.uuid4().hex[:8]}"
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(fake_id)

    def test_update_incident_status(self):
        incident_id = f"INC-{uuid.uuid4().hex[:8]}"
        created_at = datetime.now()
        status_resolved = f"RESOLVED_{uuid.uuid4().hex[:4].upper()}"

        self.tracker.register_incident(incident_id, self.random_severity, created_at)
        self.tracker.update_incident_status(incident_id, status_resolved)

        self.assertEqual(self.tracker.incidents[incident_id]["status"], status_resolved)

    def test_check_sla_breaches_warning_status(self):
        incident_id = f"INC-{uuid.uuid4().hex[:8]}"
        created_at = datetime.now()

        elapsed_seconds = int(self.random_threshold * self.warning_pct) + 1
        current_time = created_at + timedelta(seconds=elapsed_seconds)

        self.tracker.register_incident(incident_id, self.random_severity, created_at)

        breaches = self.tracker.check_sla_breaches(current_time=current_time)

        self.assertEqual(len(breaches), 1)
        self.assertEqual(breaches[0]["incident_id"], incident_id)
        self.assertEqual(breaches[0]["status"], "WARNING")

    def test_check_sla_breaches_breached_status_and_triggers(self):
        incident_id = f"INC-{uuid.uuid4().hex[:8]}"
        created_at = datetime.now()

        elapsed_seconds = self.random_threshold + random.randint(1, 100)
        current_time = created_at + timedelta(seconds=elapsed_seconds)
        
        self.tracker.register_incident(incident_id, self.random_severity, created_at)
        
        mock_notification = MagicMock()
        mock_escalation = MagicMock()
        
        breaches = self.tracker.check_sla_breaches(
            current_time=current_time,
            notification_bridge=mock_notification,
            escalation_engine=mock_escalation
        )
        
        self.assertEqual(len(breaches), 1)
        self.assertEqual(breaches[0]["incident_id"], incident_id)
        self.assertEqual(breaches[0]["status"], "BREACHED")
        
        mock_notification.notify_sla_breach.assert_called_once_with(
            incident_id=incident_id,
            severity=self.random_severity
        )
        mock_escalation.escalate_incident.assert_called_once_with(
            incident_id=incident_id,
            severity=self.random_severity
        )

    def test_check_sla_breaches_ignores_resolved(self):
        incident_id = f"INC-{uuid.uuid4().hex[:8]}"
        created_at = datetime.now()

        elapsed_seconds = self.random_threshold + 100
        current_time = created_at + timedelta(seconds=elapsed_seconds)
        
        self.tracker.register_incident(incident_id, self.random_severity, created_at)
        self.tracker.update_incident_status(incident_id, "RESOLVED_COMPLETED")
        
        breaches = self.tracker.check_sla_breaches(current_time=current_time)
        self.assertEqual(len(breaches), 0)

    def test_track_incident_sla_predicted_breach(self):
        incident_id = f"INC-{uuid.uuid4().hex[:8]}"
        threshold = random.randint(1000, 5000)
        
        now = datetime.now().replace(microsecond=0)
        elapsed = threshold + random.randint(10, 100)
        past_timestamp = int((now - timedelta(seconds=elapsed)).timestamp())

        sla_input = {
            "incident_id": incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": past_timestamp
                }
            }
        }
        
        with patch('skills.incident_sla_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = now
            mock_datetime.fromtimestamp.side_effect = lambda ts: datetime.fromtimestamp(ts)

            result = track_incident_sla(sla_input)

            self.assertEqual(result["incident_id"], incident_id)
            self.assertTrue(result["breach_predicted"])
            self.assertLess(result["time_remaining_seconds"], 0)

    def test_track_incident_sla_no_breach(self):
        incident_id = f"INC-{uuid.uuid4().hex[:8]}"
        threshold = random.randint(1000, 5000)
        
        now = datetime.now().replace(microsecond=0)
        elapsed = threshold - random.randint(100, 500)
        past_timestamp = int((now - timedelta(seconds=elapsed)).timestamp())
        
        sla_input = {
            "incident_id": incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": past_timestamp
                }
            }
        }
        
        with patch('skills.incident_sla_tracker.datetime') as mock_datetime:
            mock_datetime.now.return_value = now
            mock_datetime.fromtimestamp.side_effect = lambda ts: datetime.fromtimestamp(ts)

            result = track_incident_sla(sla_input)

            self.assertEqual(result["incident_id"], incident_id)
            self.assertFalse(result["breach_predicted"])
            self.assertGreater(result["time_remaining_seconds"], 0)
            self.assertAlmostEqual(result["time_remaining_seconds"], float(threshold - elapsed), places=2)

if __name__ == '__main__':
    unittest.main()