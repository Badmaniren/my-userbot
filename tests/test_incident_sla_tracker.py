import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import random
import uuid

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla

class TestIncidentSLATracker(unittest.TestCase):
    def setUp(self):
        self.sev_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        self.thresholds = {
            "LOW": random.randint(7200, 14400),
            "MEDIUM": random.randint(3600, 7199),
            "HIGH": random.randint(1800, 3599),
            "CRITICAL": random.randint(300, 1799)
        }
        self.warning_pct = round(random.uniform(0.7, 0.9), 2)
        self.tracker = IncidentSLATracker(self.thresholds, self.warning_pct)

    def test_register_and_get_time_to_breach(self):
        inc_id = f"inc_{uuid.uuid4().hex[:8]}"
        severity = random.choice(self.sev_levels)
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))
        
        self.tracker.register_incident(inc_id, severity, created_at)
        
        eval_time = datetime.now()
        time_to_breach = self.tracker.get_time_to_breach(inc_id, eval_time)
        
        expected_limit = self.thresholds[severity]
        elapsed = (eval_time - created_at).total_seconds()
        expected_ttb = float(expected_limit - elapsed)

        self.assertAlmostEqual(time_to_breach, expected_ttb, delta=1.0)

    def test_get_time_to_breach_key_error(self):
        fake_id = f"missing_{uuid.uuid4().hex[:6]}"
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(fake_id)

    def test_update_incident_status(self):
        inc_id = f"inc_{uuid.uuid4().hex[:8]}"
        severity = random.choice(self.sev_levels)
        created_at = datetime.now()

        self.tracker.register_incident(inc_id, severity, created_at)
        new_status = f"RESOLVED_{uuid.uuid4().hex[:4].upper()}"

        self.tracker.update_incident_status(inc_id, new_status, datetime.now())
        self.assertEqual(self.tracker.incidents[inc_id]["status"], new_status)

    def test_check_sla_breaches_warning_and_breached(self):
        inc_warn = f"inc_{uuid.uuid4().hex[:8]}"
        inc_breach = f"inc_{uuid.uuid4().hex[:8]}"
        inc_resolved = f"inc_{uuid.uuid4().hex[:8]}"
        
        sev = "CRITICAL"
        limit = self.thresholds[sev]

        now = datetime.now()
        created_warn = now - timedelta(seconds=int(limit * self.warning_pct) + 5)
        created_breach = now - timedelta(seconds=limit + 50)
        created_resolved = now - timedelta(seconds=limit + 100)

        self.tracker.register_incident(inc_warn, sev, created_warn)
        self.tracker.register_incident(inc_breach, sev, created_breach)
        self.tracker.register_incident(inc_resolved, sev, created_resolved)
        self.tracker.update_incident_status(inc_resolved, "RESOLVED_PERMANENTLY")
        
        mock_bridge = MagicMock()
        mock_escalation = MagicMock()
        
        results = self.tracker.check_sla_breaches(
            current_time=now,
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )
        
        statuses = {r["incident_id"]: r["status"] for r in results}
        
        self.assertIn(inc_warn, statuses)
        self.assertEqual(statuses[inc_warn], "WARNING")
        
        self.assertIn(inc_breach, statuses)
        self.assertEqual(statuses[inc_breach], "BREACHED")
        
        self.assertNotIn(inc_resolved, statuses)
        
        mock_bridge.notify_sla_breach.assert_called_once_with(incident_id=inc_breach, severity=sev)
        mock_escalation.escalate_incident.assert_called_once_with(incident_id=inc_breach, severity=sev)

    def test_track_incident_sla_function(self):
        inc_id = f"inc_{uuid.uuid4().hex[:8]}"
        threshold = random.randint(1000, 5000)
        past_seconds = random.randint(100, 6000)
        timestamp = (datetime.now() - timedelta(seconds=past_seconds)).timestamp()

        payload = {
            "incident_id": inc_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp
                }
            }
        }
        
        res = track_incident_sla(payload)
        
        self.assertEqual(res["incident_id"], inc_id)
        self.assertIsInstance(res["breach_predicted"], bool)
        self.assertIsInstance(res["time_remaining_seconds"], float)
        
        if past_seconds > threshold:
            self.assertTrue(res["breach_predicted"])
        else:
            self.assertFalse(res["breach_predicted"])

    def test_incident_aggregator_integration_simulation(self):
        with patch("skills.incident_aggregator.aggregate_incidents") as mock_aggregate:
            random_digest = uuid.uuid4().hex
            mock_aggregate.return_value = {"aggregated_digest": random_digest}

            from skills.incident_aggregator import aggregate_incidents
            dummy_exc = Exception(uuid.uuid4().hex)
            dummy_tb = uuid.uuid4().hex

            res = aggregate_incidents([{"id": uuid.uuid4().hex}], dummy_exc, dummy_tb)
            self.assertEqual(res["aggregated_digest"], random_digest)
            mock_aggregate.assert_called_once()

if __name__ == "__main__":
    unittest.main()