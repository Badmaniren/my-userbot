import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid
import random
import string

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla


class TestIncidentSLATracker(unittest.TestCase):

    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))
        self.thresholds = {
            "LOW": random.randint(7200, 10000),
            "MEDIUM": random.randint(3600, 7199),
            "HIGH": random.randint(1800, 3599),
            "CRITICAL": random.randint(300, 1799)
        }
        self.warning_pct = round(random.uniform(0.5, 0.8), 2)
        self.tracker = IncidentSLATracker(self.thresholds, self.warning_pct)

    def test_register_and_get_time_to_breach(self):
        self.tracker.register_incident(self.incident_id, self.severity, self.created_at)
        
        current_time = datetime.now()
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id, current_time)
        
        expected_limit = self.thresholds.get(self.severity, 3600)
        expected_elapsed = (current_time - self.created_at).total_seconds()
        expected_result = float(expected_limit - expected_elapsed)

        self.assertAlmostEqual(time_to_breach, expected_result, delta=1.0)

    def test_get_time_to_breach_not_found(self):
        unknown_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(unknown_id)

    def test_update_incident_status(self):
        self.tracker.register_incident(self.incident_id, self.severity, self.created_at)
        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"

        self.tracker.update_incident_status(self.incident_id, new_status)

        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], new_status)

    def test_check_sla_breaches_warning(self):
        limit = 100
        self.tracker.sla_thresholds[self.severity] = limit
        self.tracker.warning_threshold_pct = 0.5

        past_time = datetime.now() - timedelta(seconds=60)
        self.tracker.register_incident(self.incident_id, self.severity, past_time)

        results = self.tracker.check_sla_breaches()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["incident_id"], self.incident_id)
        self.assertEqual(results[0]["status"], "WARNING")

    def test_check_sla_breaches_breached_with_notifications(self):
        limit = 50
        self.tracker.sla_thresholds[self.severity] = limit
        
        past_time = datetime.now() - timedelta(seconds=120)
        self.tracker.register_incident(self.incident_id, self.severity, past_time)
        
        mock_notification_bridge = MagicMock()
        mock_escalation_engine = MagicMock()
        
        results = self.tracker.check_sla_breaches(
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
        limit = 50
        self.tracker.sla_thresholds[self.severity] = limit
        
        past_time = datetime.now() - timedelta(seconds=120)
        self.tracker.register_incident(self.incident_id, self.severity, past_time)
        self.tracker.update_incident_status(self.incident_id, "RESOLVED_SUCCESS")
        
        results = self.tracker.check_sla_breaches()
        self.assertEqual(len(results), 0)

    def test_track_incident_sla_function(self):
        timestamp = int(datetime.now().timestamp()) - 200
        threshold = 100
        
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
        self.assertTrue(res["breach_predicted"])
        self.assertIsInstance(res["time_remaining_seconds"], float)

    def test_end_to_end_sla_tracker_integration(self):
        with patch("skills.incident_sla_tracker.datetime") as mock_dt:
            fixed_now = datetime(2025, 1, 1, 12, 0, 0)
            mock_dt.now.return_value = fixed_now
            mock_dt.fromtimestamp.side_effect = datetime.fromtimestamp

            self.tracker.register_incident(self.incident_id, self.severity, fixed_now - timedelta(seconds=10))

            time_rem = self.tracker.get_time_to_breach(self.incident_id, fixed_now)
            expected_limit = self.thresholds.get(self.severity, 3600)
            self.assertEqual(time_rem, float(expected_limit - 10))


if __name__ == "__main__":
    unittest.main()