import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import random
import uuid

from skills.incident_sla_tracker import (
    IncidentSLATracker,
    track_incident_sla,
)


class TestIncidentSLATracker(unittest.TestCase):

    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.thresholds = {
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 600
        }
        self.warning_pct = 0.8
        self.tracker = IncidentSLATracker(
            sla_thresholds=self.thresholds,
            warning_threshold_pct=self.warning_pct
        )

    def test_register_incident(self):
        now = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, now)
        
        self.assertIn(self.incident_id, self.tracker.incidents)
        incident_data = self.tracker.incidents[self.incident_id]
        self.assertEqual(incident_data["severity"], self.severity)
        self.assertEqual(incident_data["created_at"], now)
        self.assertEqual(incident_data["status"], "ACTIVE")

    def test_get_time_to_breach_success(self):
        created_at = datetime.now() - timedelta(seconds=100)
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        current_time = created_at + timedelta(seconds=500)
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id, current_time)
        
        expected_limit = self.thresholds[self.severity]
        expected_elapsed = 500
        self.assertEqual(time_to_breach, expected_limit - expected_elapsed)

    def test_get_time_to_breach_not_found(self):
        fake_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(fake_id)

    def test_update_incident_status(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"
        self.tracker.update_incident_status(self.incident_id, new_status)
        
        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], new_status)

    def test_check_sla_breaches_warning(self):
        created_at = datetime.now() - timedelta(seconds=2900)
        self.tracker.register_incident(self.incident_id, "MEDIUM", created_at)
        
        current_time = datetime.now()
        results = self.tracker.check_sla_breaches(current_time=current_time)
        
        self.assertTrue(any(r["incident_id"] == self.incident_id and r["status"] == "WARNING" for r in results))

    def test_check_sla_breaches_breached(self):
        created_at = datetime.now() - timedelta(seconds=4000)
        self.tracker.register_incident(self.incident_id, "MEDIUM", created_at)
        
        mock_bridge = MagicMock()
        mock_escalation = MagicMock()
        
        current_time = datetime.now()
        results = self.tracker.check_sla_breaches(
            current_time=current_time,
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )
        
        self.assertTrue(any(r["incident_id"] == self.incident_id and r["status"] == "BREACHED" for r in results))
        mock_bridge.notify_sla_breach.assert_called_once_with(incident_id=self.incident_id, severity="MEDIUM")
        mock_escalation.escalate_incident.assert_called_once_with(incident_id=self.incident_id, severity="MEDIUM")

    def test_check_sla_breaches_resolved_ignored(self):
        created_at = datetime.now() - timedelta(seconds=5000)
        self.tracker.register_incident(self.incident_id, "MEDIUM", created_at)
        self.tracker.update_incident_status(self.incident_id, "RESOLVED_SUCCESS")
        
        results = self.tracker.check_sla_breaches()
        self.assertEqual(len(results), 0)

    def test_track_incident_sla_function_with_timestamp(self):
        random_id = uuid.uuid4().hex
        past_timestamp = int(datetime.now().timestamp()) - 1500
        threshold = 3600
        
        sla_input = {
            "incident_id": random_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": past_timestamp
                }
            }
        }
        
        result = track_incident_sla(sla_input)
        
        self.assertEqual(result["incident_id"], random_id)
        self.assertFalse(result["breach_predicted"])
        self.assertIsInstance(result["time_remaining_seconds"], float)

    def test_track_incident_sla_function_without_timestamp(self):
        random_id = uuid.uuid4().hex
        threshold = 100
        
        sla_input = {
            "incident_id": random_id,
            "threshold_seconds": threshold,
            "aggregated_data": {}
        }
        
        result = track_incident_sla(sla_input)
        
        self.assertEqual(result["incident_id"], random_id)
        self.assertIsInstance(result["breach_predicted"], bool)
        self.assertIsInstance(result["time_remaining_seconds"], float)


class TestIncidentSLATrackerIntegrationSafe(unittest.TestCase):

    def test_integration_flow_with_mocks(self):
        random_inc_id = uuid.uuid4().hex
        severity_level = random.choice(["HIGH", "CRITICAL"])
        
        tracker = IncidentSLATracker(
            sla_thresholds={"HIGH": 1000, "CRITICAL": 500},
            warning_threshold_pct=0.5
        )
        
        created_time = datetime.now() - timedelta(seconds=1200)
        tracker.register_incident(random_inc_id, severity_level, created_time)
        
        fixed_now = created_time + timedelta(seconds=1200)
        mock_bridge = MagicMock()
        mock_engine = MagicMock()

        breaches = tracker.check_sla_breaches(
            current_time=fixed_now,
            notification_bridge=mock_bridge,
            escalation_engine=mock_engine
        )

        self.assertEqual(len(breaches), 1)
        self.assertEqual(breaches[0]["incident_id"], random_inc_id)
        self.assertEqual(breaches[0]["status"], "BREACHED")
        mock_bridge.notify_sla_breach.assert_called_once()
        mock_engine.escalate_incident.assert_called_once()


if __name__ == "__main__":
    unittest.main()