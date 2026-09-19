import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid
import random
import string

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla


class TestIncidentSLATracker(unittest.TestCase):
    def setUp(self):
        self.severity_levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        self.random_thresholds = {
            "CRITICAL": random.randint(300, 1800),
            "HIGH": random.randint(1801, 3600),
            "MEDIUM": random.randint(3601, 7200),
            "LOW": random.randint(7201, 14400)
        }
        self.random_warning_pct = round(random.uniform(0.5, 0.8), 2)
        self.tracker = IncidentSLATracker(
            sla_thresholds=self.random_thresholds,
            warning_threshold_pct=self.random_warning_pct
        )

    def test_register_incident_success(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(self.severity_levels)
        created_at = datetime.now() - timedelta(seconds=random.randint(1, 100))

        self.tracker.register_incident(incident_id, severity, created_at)

        self.assertIn(incident_id, self.tracker.incidents)
        self.assertEqual(self.tracker.incidents[incident_id]["severity"], severity)
        self.assertEqual(self.tracker.incidents[incident_id]["created_at"], created_at)
        self.assertEqual(self.tracker.incidents[incident_id]["status"], "ACTIVE")

    def test_get_time_to_breach_success(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(self.severity_levels)
        created_at = datetime.now() - timedelta(seconds=50)
        
        self.tracker.register_incident(incident_id, severity, created_at)
        
        current_time = created_at + timedelta(seconds=100)
        time_to_breach = self.tracker.get_time_to_breach(incident_id, current_time=current_time)
        
        expected_limit = self.random_thresholds[severity]
        expected_elapsed = 100.0
        self.assertEqual(time_to_breach, float(expected_limit - expected_elapsed))

    def test_get_time_to_breach_raises_key_error(self):
        missing_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(missing_id)

    def test_update_incident_status(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(self.severity_levels)
        created_at = datetime.now()
        new_status = "".join(random.choices(string.ascii_uppercase, k=8))

        self.tracker.register_incident(incident_id, severity, created_at)
        self.tracker.update_incident_status(incident_id, new_status)

        self.assertEqual(self.tracker.incidents[incident_id]["status"], new_status)

    def test_check_sla_breaches_warning_and_breach(self):
        crit_id = uuid.uuid4().hex
        high_id = uuid.uuid4().hex
        resolved_id = uuid.uuid4().hex
        
        base_time = datetime.now()
        
        self.tracker.register_incident(crit_id, "CRITICAL", base_time - timedelta(seconds=self.random_thresholds["CRITICAL"] + 10))
        
        warning_elapsed = int(self.random_thresholds["HIGH"] * self.random_warning_pct) + 5
        self.tracker.register_incident(high_id, "HIGH", base_time - timedelta(seconds=warning_elapsed))
        
        self.tracker.register_incident(resolved_id, "MEDIUM", base_time - timedelta(seconds=10000))
        self.tracker.update_incident_status(resolved_id, "RESOLVED")

        mock_notification_bridge = MagicMock()
        mock_escalation_engine = MagicMock()

        results = self.tracker.check_sla_breaches(
            current_time=base_time,
            notification_bridge=mock_notification_bridge,
            escalation_engine=mock_escalation_engine
        )

        mock_notification_bridge.notify_sla_breach.assert_called_once_with(incident_id=crit_id, severity="CRITICAL")
        mock_escalation_engine.escalate_incident.assert_called_once_with(incident_id=crit_id, severity="CRITICAL")

        result_map = {res["incident_id"]: res["status"] for res in results}
        self.assertIn(crit_id, result_map)
        self.assertEqual(result_map[crit_id], "BREACHED")
        self.assertIn(high_id, result_map)
        self.assertEqual(result_map[high_id], "WARNING")
        self.assertNotIn(resolved_id, result_map)

    def test_track_incident_sla_function_breached(self):
        incident_id = uuid.uuid4().hex
        threshold = random.randint(500, 1000)
        past_timestamp = int(datetime.now().timestamp()) - (threshold + random.randint(10, 100))
        
        sla_input = {
            "incident_id": incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": past_timestamp
                }
            }
        }

        result = track_incident_sla(sla_input)

        self.assertEqual(result["incident_id"], incident_id)
        self.assertTrue(result["breach_predicted"])
        self.assertLess(result["time_remaining_seconds"], 0)

    def test_track_incident_sla_function_safe(self):
        incident_id = uuid.uuid4().hex
        threshold = random.randint(5000, 10000)
        recent_timestamp = int(datetime.now().timestamp())
        
        sla_input = {
            "incident_id": incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": recent_timestamp
                }
            }
        }

        result = track_incident_sla(sla_input)

        self.assertEqual(result["incident_id"], incident_id)
        self.assertFalse(result["breach_predicted"])
        self.assertGreater(result["time_remaining_seconds"], 0)


if __name__ == "__main__":
    unittest.main()