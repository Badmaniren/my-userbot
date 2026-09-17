import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid
import random
from skills.incident_sla_tracker import IncidentSLATracker

class TestIncidentSLATracker(unittest.TestCase):
    def setUp(self):
        self.severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        self.thresholds = {s: random.randint(60, 3600) for s in self.severities}
        self.warning_pct = random.uniform(0.5, 0.9)
        self.tracker = IncidentSLATracker(self.thresholds, self.warning_pct)

    def test_register_and_get_time_to_breach(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(self.severities)
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 50))
        
        self.tracker.register_incident(incident_id, severity, created_at)
        
        current_time = datetime.now()
        expected_limit = self.thresholds[severity]
        elapsed = (current_time - created_at).total_seconds()
        expected_remaining = float(expected_limit - elapsed)
        
        actual_remaining = self.tracker.get_time_to_breach(incident_id, current_time)
        self.assertAlmostEqual(actual_remaining, expected_remaining, places=2)

    def test_get_time_to_breach_key_error(self):
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(uuid.uuid4().hex)

    def test_update_incident_status(self):
        incident_id = uuid.uuid4().hex
        new_status = uuid.uuid4().hex
        self.tracker.register_incident(incident_id, random.choice(self.severities), datetime.now())

        self.tracker.update_incident_status(incident_id, new_status)
        self.assertEqual(self.tracker.incidents[incident_id]["status"], new_status)

    def test_check_sla_breaches_logic(self):
        incident_id_breach = uuid.uuid4().hex
        incident_id_warn = uuid.uuid4().hex

        severity = "CRITICAL"
        limit = self.thresholds[severity]
        
        # Breach case
        self.tracker.register_incident(incident_id_breach, severity, datetime.now() - timedelta(seconds=limit + 10))
        # Warning case
        self.tracker.register_incident(incident_id_warn, severity, datetime.now() - timedelta(seconds=limit * self.warning_pct + 1))
        
        mock_bridge = MagicMock()
        mock_escalation = MagicMock()
        
        results = self.tracker.check_sla_breaches(
            current_time=datetime.now(),
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )
        
        breach_found = any(r["incident_id"] == incident_id_breach and r["status"] == "BREACHED" for r in results)
        warn_found = any(r["incident_id"] == incident_id_warn and r["status"] == "WARNING" for r in results)
        
        self.assertTrue(breach_found)
        self.assertTrue(warn_found)
        mock_bridge.notify_sla_breach.assert_called_with(incident_id=incident_id_breach, severity=severity)
        mock_escalation.escalate_incident.assert_called_with(incident_id=incident_id_breach, severity=severity)

    def test_check_sla_breaches_resolved_ignored(self):
        incident_id = uuid.uuid4().hex
        self.tracker.register_incident(incident_id, random.choice(self.severities), datetime.now() - timedelta(hours=24))
        self.tracker.update_incident_status(incident_id, "RESOLVED_BY_SYSTEM")
        
        results = self.tracker.check_sla_breaches()
        self.assertEqual(len(results), 0)

    def test_integration_with_external_mocks(self):
        with patch('skills.incident_notification_bridge') as mock_bridge:
            with patch('skills.incident_auto_escalation_engine') as mock_engine:
                incident_id = uuid.uuid4().hex
                self.tracker.register_incident(incident_id, "CRITICAL", datetime.now() - timedelta(seconds=5000))

                results = self.tracker.check_sla_breaches(
                    notification_bridge=mock_bridge,
                    escalation_engine=mock_engine
                )

                self.assertGreater(len(results), 0)
                self.assertEqual(results[0]["incident_id"], incident_id)

if __name__ == '__main__':
    unittest.main()