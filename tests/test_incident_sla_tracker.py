import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid
import random

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla


class TestIncidentSLATracker(unittest.TestCase):

    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.thresholds = {
            "LOW": random.randint(7200, 14400),
            "MEDIUM": random.randint(3600, 7199),
            "HIGH": random.randint(1800, 3599),
            "CRITICAL": random.randint(300, 1799)
        }
        self.warning_pct = round(random.uniform(0.5, 0.9), 2)
        self.tracker = IncidentSLATracker(self.thresholds, self.warning_pct)

    def test_register_incident(self):
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        self.assertIn(self.incident_id, self.tracker.incidents)
        incident = self.tracker.incidents[self.incident_id]
        self.assertEqual(incident["severity"], self.severity)
        self.assertEqual(incident["created_at"], created_at)
        self.assertEqual(incident["status"], "ACTIVE")

    def test_get_time_to_breach_success(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        future_time = created_at + timedelta(seconds=100)
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id, current_time=future_time)

        expected_limit = self.thresholds.get(self.severity, 3600)
        self.assertEqual(time_to_breach, expected_limit - 100)

    def test_get_time_to_breach_not_found(self):
        missing_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(missing_id)

    def test_update_incident_status(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"
        self.tracker.update_incident_status(self.incident_id, new_status)

        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], new_status)

    def test_check_sla_breaches_warning(self):
        created_at = datetime.now()
        sla_limit = self.thresholds.get(self.severity, 3600)
        elapsed_for_warning = int(sla_limit * self.warning_pct) + random.randint(1, 10)
        
        simulated_current_time = created_at + timedelta(seconds=elapsed_for_warning)
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        results = self.tracker.check_sla_breaches(current_time=simulated_current_time)
        
        self.assertTrue(any(r["incident_id"] == self.incident_id and r["status"] == "WARNING" for r in results))

    def test_check_sla_breaches_breached(self):
        created_at = datetime.now()
        sla_limit = self.thresholds.get(self.severity, 3600)
        elapsed_for_breach = sla_limit + random.randint(10, 500)
        
        simulated_current_time = created_at + timedelta(seconds=elapsed_for_breach)
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        mock_notification = MagicMock()
        mock_escalation = MagicMock()

        results = self.tracker.check_sla_breaches(
            current_time=simulated_current_time,
            notification_bridge=mock_notification,
            escalation_engine=mock_escalation
        )

        mock_notification.notify_sla_breach.assert_called_once_with(
            incident_id=self.incident_id, severity=self.severity
        )
        mock_escalation.escalate_incident.assert_called_once_with(
            incident_id=self.incident_id, severity=self.severity
        )
        self.assertTrue(any(r["incident_id"] == self.incident_id and r["status"] == "BREACHED" for r in results))

    def test_check_sla_breaches_resolved_skipped(self):
        created_at = datetime.now()
        sla_limit = self.thresholds.get(self.severity, 3600)
        simulated_current_time = created_at + timedelta(seconds=sla_limit + 1000)
        
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        self.tracker.update_incident_status(self.incident_id, "RESOLVED_SUCCESS")

        results = self.tracker.check_sla_breaches(current_time=simulated_current_time)
        self.assertNotIn(self.incident_id, [r["incident_id"] for r in results])

    def test_track_incident_sla_function(self):
        timestamp = int(datetime.now().timestamp()) - random.randint(100, 1000)
        threshold_seconds = random.randint(1800, 7200)
        
        sla_input = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold_seconds,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp
                }
            }
        }

        result = track_incident_sla(sla_input)

        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIsInstance(result["breach_predicted"], bool)
        self.assertIsInstance(result["time_remaining_seconds"], float)

    def test_sla_tracker_integration_workflow(self):
        with patch("skills.incident_sla_tracker.aggregate_incidents") as mock_aggregate:
            mock_aggregate.return_value = {uuid.uuid4().hex: random.randint(1, 5)}
            
            created_at = datetime.now() - timedelta(seconds=random.randint(50, 500))
            self.tracker.register_incident(self.incident_id, self.severity, created_at)
            
            time_to_breach = self.tracker.get_time_to_breach(self.incident_id)
            self.assertIsInstance(time_to_breach, float)
            
            status_list = self.tracker.check_sla_breaches()
            self.assertIsInstance(status_list, list)