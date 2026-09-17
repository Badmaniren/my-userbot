import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid
import random
import string

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla


class TestIncidentSLATracker(unittest.TestCase):

    def setUp(self):
        self.rand_str = lambda: uuid.uuid4().hex[:8]
        self.severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        self.thresholds = {
            "LOW": random.randint(7200, 10800),
            "MEDIUM": random.randint(3600, 7199),
            "HIGH": random.randint(1800, 3599),
            "CRITICAL": random.randint(300, 1799)
        }
        self.warning_pct = random.uniform(0.5, 0.8)
        self.tracker = IncidentSLATracker(self.thresholds, self.warning_pct)

    def test_register_and_time_to_breach_success(self):
        incident_id = f"inc_{self.rand_str()}"
        severity = random.choice(self.severities)
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))

        self.tracker.register_incident(incident_id, severity, created_at)
        
        current_time = datetime.now()
        time_to_breach = self.tracker.get_time_to_breach(incident_id, current_time)
        
        expected_limit = self.thresholds[severity]
        elapsed = (current_time - created_at).total_seconds()
        expected_breach_time = float(expected_limit - elapsed)

        self.assertAlmostEqual(time_to_breach, expected_breach_time, delta=2.0)

    def test_get_time_to_breach_not_found(self):
        missing_id = f"missing_{self.rand_str()}"
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(missing_id)

    def test_update_incident_status(self):
        incident_id = f"inc_{self.rand_str()}"
        severity = random.choice(self.severities)
        created_at = datetime.now()

        self.tracker.register_incident(incident_id, severity, created_at)
        
        new_status = f"RESOLVED_{self.rand_str()}"
        self.tracker.update_incident_status(incident_id, new_status)

        self.assertEqual(self.tracker.incidents[incident_id]["status"], new_status)

    def test_check_sla_breaches_active_warning_and_breach(self):
        inc_breached_id = f"inc_{self.rand_str()}"
        inc_warning_id = f"inc_{self.rand_str()}"
        inc_resolved_id = f"inc_{self.rand_str()}"

        sev_breached = "CRITICAL"
        sev_warning = "HIGH"
        sev_resolved = "LOW"

        limit_breached = self.thresholds[sev_breached]
        limit_warning = self.thresholds[sev_warning]

        now = datetime.now()
        created_breached = now - timedelta(seconds=limit_breached + random.randint(10, 500))
        created_warning = now - timedelta(seconds=int(limit_warning * self.warning_pct) + 10)
        created_resolved = now - timedelta(seconds=limit_breached * 2)

        self.tracker.register_incident(inc_breached_id, sev_breached, created_breached)
        self.tracker.register_incident(inc_warning_id, sev_warning, created_warning)
        self.tracker.register_incident(inc_resolved_id, sev_resolved, created_resolved)
        self.tracker.update_incident_status(inc_resolved_id, "RESOLVED_SUCCESS")

        mock_notification = MagicMock()
        mock_escalation = MagicMock()

        results = self.tracker.check_sla_breaches(
            current_time=now,
            notification_bridge=mock_notification,
            escalation_engine=mock_escalation
        )

        result_map = {item["incident_id"]: item["status"] for item in results}

        self.assertIn(inc_breached_id, result_map)
        self.assertEqual(result_map[inc_breached_id], "BREACHED")

        self.assertIn(inc_warning_id, result_map)
        self.assertEqual(result_map[inc_warning_id], "WARNING")

        self.assertNotIn(inc_resolved_id, result_map)

        mock_notification.notify_sla_breach.assert_called_once_with(
            incident_id=inc_breached_id, severity=sev_breached
        )
        mock_escalation.escalate_incident.assert_called_once_with(
            incident_id=inc_breached_id, severity=sev_breached
        )

    def test_track_incident_sla_function_prediction(self):
        incident_id = f"inc_func_{self.rand_str()}"
        threshold = random.randint(1000, 5000)
        timestamp_diff = random.randint(100, 2000)
        timestamp = int(datetime.now().timestamp()) - timestamp_diff

        sla_input = {
            "incident_id": incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp
                }
            }
        }

        result = track_incident_sla(sla_input)

        self.assertEqual(result["incident_id"], incident_id)
        self.assertIsInstance(result["breach_predicted"], bool)
        self.assertIsInstance(result["time_remaining_seconds"], float)

        expected_remaining = threshold - timestamp_diff
        self.assertAlmostEqual(result["time_remaining_seconds"], expected_remaining, delta=5.0)


if __name__ == "__main__":
    unittest.main()