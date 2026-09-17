import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid
import random
from skills.incident_sla_tracker import IncidentSLATracker

class TestIncidentSLATracker(unittest.TestCase):
    def setUp(self):
        self.random_id = uuid.uuid4().hex
        self.random_severity = random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"])
        self.sla_thresholds = {self.random_severity: random.randint(60, 3600)}
        self.warning_pct = random.uniform(0.5, 0.9)
        self.tracker = IncidentSLATracker(self.sla_thresholds, self.warning_pct)

    def test_register_and_get_time_to_breach(self):
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 50))
        self.tracker.register_incident(self.random_id, self.random_severity, created_at)
        
        breach_time = self.tracker.get_time_to_breach(self.random_id)
        expected_limit = self.sla_thresholds[self.random_severity]
        
        self.assertIsInstance(breach_time, float)
        self.assertTrue(breach_time < expected_limit)

    def test_check_sla_breaches_trigger_notification(self):
        created_at = datetime.now() - timedelta(seconds=3600)
        self.tracker.register_incident(self.random_id, self.random_severity, created_at)
        
        mock_bridge = MagicMock()
        mock_escalation = MagicMock()
        
        with patch('skills.incident_sla_tracker.datetime') as mock_date:
            mock_date.now.return_value = datetime.now()

            results = self.tracker.check_sla_breaches(
                current_time=datetime.now(),
                notification_bridge=mock_bridge,
                escalation_engine=mock_escalation
            )

            self.assertEqual(results[0]["incident_id"], self.random_id)
            self.assertEqual(results[0]["status"], "BREACHED")
            mock_bridge.notify_sla_breach.assert_called_once_with(
                incident_id=self.random_id,
                severity=self.random_severity
            )
            mock_escalation.escalate_incident.assert_called_once_with(
                incident_id=self.random_id,
                severity=self.random_severity
            )

    def test_update_incident_status_persistence(self):
        new_status = f"RESOLVED_{uuid.uuid4().hex[:5]}"
        self.tracker.register_incident(self.random_id, self.random_severity, datetime.now())
        self.tracker.update_incident_status(self.random_id, new_status)
        
        self.assertEqual(self.tracker.incidents[self.random_id]["status"], new_status)

    def test_warning_threshold_logic(self):
        threshold = 1000
        self.tracker.sla_thresholds = {self.random_severity: threshold}
        self.tracker.warning_threshold_pct = 0.5
        
        # Elapsed 600s (60% of 1000, which is > 50% warning)
        created_at = datetime.now() - timedelta(seconds=600)
        self.tracker.register_incident(self.random_id, self.random_severity, created_at)
        
        results = self.tracker.check_sla_breaches(current_time=datetime.now())
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "WARNING")

    def test_non_existent_incident_raises_keyerror(self):
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(uuid.uuid4().hex)

if __name__ == '__main__':
    unittest.main()