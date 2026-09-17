import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid
import random
import string

from skills.incident_sla_tracker import IncidentSLATracker

class TestIncidentSLATracker(unittest.TestCase):

    def setUp(self):
        self.random_severity = random.choice(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'])
        self.random_threshold = random.randint(60, 3600)
        self.random_warning_pct = random.uniform(0.5, 0.9)
        self.tracker = IncidentSLATracker(
            sla_thresholds={self.random_severity: self.random_threshold},
            warning_threshold_pct=self.random_warning_pct
        )

    def test_register_and_get_time_to_breach(self):
        incident_id = uuid.uuid4().hex
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 50))

        self.tracker.register_incident(incident_id, self.random_severity, created_at)

        current_time = datetime.now()
        expected_remaining = self.random_threshold - (current_time - created_at).total_seconds()
        actual_remaining = self.tracker.get_time_to_breach(incident_id, current_time)

        self.assertAlmostEqual(actual_remaining, expected_remaining, delta=0.1)

    def test_get_time_to_breach_raises_key_error(self):
        fake_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(fake_id)

    def test_check_sla_breaches_logic(self):
        incident_id = uuid.uuid4().hex
        # Создаем инцидент, который гарантированно нарушил SLA
        created_at = datetime.now() - timedelta(seconds=self.random_threshold + random.randint(1, 100))

        self.tracker.register_incident(incident_id, self.random_severity, created_at)

        mock_bridge = MagicMock()
        mock_escalation = MagicMock()

        results = self.tracker.check_sla_breaches(
            current_time=datetime.now(),
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["incident_id"], incident_id)
        self.assertEqual(results[0]["status"], "BREACHED")

        mock_bridge.notify_sla_breach.assert_called_once_with(incident_id=incident_id, severity=self.random_severity)
        mock_escalation.escalate_incident.assert_called_once_with(incident_id=incident_id, severity=self.random_severity)

    def test_update_incident_status_persistence(self):
        incident_id = uuid.uuid4().hex
        new_status = ''.join(random.choices(string.ascii_uppercase, k=10))

        self.tracker.register_incident(incident_id, self.random_severity, datetime.now())
        self.tracker.update_incident_status(incident_id, new_status)

        self.assertEqual(self.tracker.incidents[incident_id]["status"], new_status)

    def test_resolved_incidents_ignored_in_breach_check(self):
        incident_id = uuid.uuid4().hex
        created_at = datetime.now() - timedelta(seconds=self.random_threshold + 100)

        self.tracker.register_incident(incident_id, self.random_severity, created_at)
        self.tracker.update_incident_status(incident_id, "RESOLVED_" + uuid.uuid4().hex)

        results = self.tracker.check_sla_breaches()
        self.assertEqual(len(results), 0)

    def test_warning_threshold_logic(self):
        incident_id = uuid.uuid4().hex
        # Устанавливаем время так, чтобы оно попало в зону WARNING (между threshold * pct и threshold)
        elapsed_time = int(self.random_threshold * ((1 + self.random_warning_pct) / 2))
        created_at = datetime.now() - timedelta(seconds=elapsed_time)

        self.tracker.register_incident(incident_id, self.random_severity, created_at)

        results = self.tracker.check_sla_breaches()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "WARNING")

if __name__ == '__main__':
    unittest.main()