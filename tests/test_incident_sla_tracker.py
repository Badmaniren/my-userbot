import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import random
import uuid

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla

class TestIncidentSLATracker(unittest.TestCase):
    def setUp(self):
        self.severity_levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        self.thresholds = {
            "CRITICAL": random.randint(300, 900),
            "HIGH": random.randint(1800, 3600),
            "MEDIUM": random.randint(7200, 14400),
            "LOW": random.randint(28800, 86400)
        }
        self.warning_pct = round(random.uniform(0.5, 0.9), 2)
        self.tracker = IncidentSLATracker(self.thresholds, self.warning_pct)

    def test_register_and_get_time_to_breach(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(self.severity_levels)
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))
        
        self.tracker.register_incident(incident_id, severity, created_at)
        
        current_time = datetime.now()
        time_to_breach = self.tracker.get_time_to_breach(incident_id, current_time)

        expected_limit = self.thresholds[severity]
        expected_elapsed = (current_time - created_at).total_seconds()
        expected_remaining = float(expected_limit - expected_elapsed)
        
        self.assertAlmostEqual(time_to_breach, expected_remaining, delta=1.0)

    def test_get_time_to_breach_nonexistent_raises_key_error(self):
        missing_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(missing_id)

    def test_update_incident_status(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(self.severity_levels)
        created_at = datetime.now()
        
        self.tracker.register_incident(incident_id, severity, created_at)
        
        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"
        self.tracker.update_incident_status(incident_id, new_status)

        self.assertEqual(self.tracker.incidents[incident_id]["status"], new_status)

    def test_check_sla_breaches_warning_and_breached(self):
        inc_breached = uuid.uuid4().hex
        inc_warning = uuid.uuid4().hex
        inc_normal = uuid.uuid4().hex
        inc_resolved = uuid.uuid4().hex

        sev_b = random.choice(self.severity_levels)
        sev_w = random.choice(self.severity_levels)
        sev_n = random.choice(self.severity_levels)
        sev_r = random.choice(self.severity_levels)

        now = datetime.now()

        limit_b = self.thresholds[sev_b]
        limit_w = self.thresholds[sev_w]

        created_b = now - timedelta(seconds=limit_b + random.randint(10, 500))
        created_w = now - timedelta(seconds=int(limit_w * self.warning_pct) + 10)
        created_n = now - timedelta(seconds=5)
        created_r = now - timedelta(seconds=limit_b * 2)

        self.tracker.register_incident(inc_breached, sev_b, created_b)
        self.tracker.register_incident(inc_warning, sev_w, created_w)
        self.tracker.register_incident(inc_normal, sev_n, created_n)
        self.tracker.register_incident(inc_resolved, sev_r, created_r)
        self.tracker.update_incident_status(inc_resolved, "RESOLVED")

        mock_bridge = MagicMock()
        mock_escalation = MagicMock()

        results = self.tracker.check_sla_breaches(
            current_time=now,
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )

        statuses = {res["incident_id"]: res["status"] for res in results}

        self.assertIn(inc_breached, statuses)
        self.assertEqual(statuses[inc_breached], "BREACHED")
        self.assertIn(inc_warning, statuses)
        self.assertEqual(statuses[inc_warning], "WARNING")
        self.assertNotIn(inc_normal, statuses)
        self.assertNotIn(inc_resolved, statuses)

        mock_bridge.notify_sla_breach.assert_called_once_with(incident_id=inc_breached, severity=sev_b)
        mock_escalation.escalate_incident.assert_called_once_with(incident_id=inc_breached, severity=sev_b)

    def test_track_incident_sla_function_valid(self):
        incident_id = uuid.uuid4().hex
        threshold = random.randint(1000, 5000)
        past_seconds = random.randint(100, threshold - 10)
        timestamp = int(datetime.now().timestamp() - past_seconds)

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
        self.assertFalse(result["breach_predicted"])
        self.assertGreater(result["time_remaining_seconds"], 0)

    def test_track_incident_sla_function_breached(self):
        incident_id = uuid.uuid4().hex
        threshold = random.randint(100, 500)
        past_seconds = threshold + random.randint(50, 200)
        timestamp = int(datetime.now().timestamp() - past_seconds)

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
        self.assertTrue(result["breach_predicted"])
        self.assertLess(result["time_remaining_seconds"], 0)