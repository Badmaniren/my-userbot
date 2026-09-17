import unittest
from unittest.mock import MagicMock, patch
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
            "CRITICAL": random.randint(60, 1799)
        }
        self.warning_pct = round(random.uniform(0.5, 0.8), 2)
        self.tracker = IncidentSLATracker(
            sla_thresholds=self.thresholds,
            warning_threshold_pct=self.warning_pct
        )

    def test_register_and_get_time_to_breach(self):
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 50))
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        current_time = datetime.now()
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id, current_time)

        expected_limit = self.thresholds[self.severity]
        elapsed = (current_time - created_at).total_seconds()
        expected_remaining = float(expected_limit - elapsed)
        
        self.assertAlmostEqual(time_to_breach, expected_remaining, delta=1.0)

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

    def test_check_sla_breaches_warning_and_breach(self):
        now = datetime.now()

        breach_id = uuid.uuid4().hex
        warning_id = uuid.uuid4().hex
        active_id = uuid.uuid4().hex
        resolved_id = uuid.uuid4().hex
        
        limit = 1000
        self.tracker.sla_thresholds[self.severity] = limit
        self.tracker.warning_threshold_pct = 0.5

        self.tracker.register_incident(breach_id, self.severity, now - timedelta(seconds=1200))
        self.tracker.register_incident(warning_id, self.severity, now - timedelta(seconds=600))
        self.tracker.register_incident(active_id, self.severity, now - timedelta(seconds=100))
        self.tracker.register_incident(resolved_id, self.severity, now - timedelta(seconds=1500))
        self.tracker.update_incident_status(resolved_id, "RESOLVED_COMPLETED")
        
        mock_bridge = MagicMock()
        mock_escalation = MagicMock()
        
        results = self.tracker.check_sla_breaches(
            current_time=now,
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )
        
        result_map = {item["incident_id"]: item["status"] for item in results}
        
        self.assertIn(breach_id, result_map)
        self.assertEqual(result_map[breach_id], "BREACHED")

        self.assertIn(warning_id, result_map)
        self.assertEqual(result_map[warning_id], "WARNING")
        
        self.assertNotIn(active_id, result_map)
        self.assertNotIn(resolved_id, result_map)
        
        mock_bridge.notify_sla_breach.assert_called_once_with(incident_id=breach_id, severity=self.severity)
        mock_escalation.escalate_incident.assert_called_once_with(incident_id=breach_id, severity=self.severity)

    def test_track_incident_sla_with_timestamp(self):
        threshold = random.randint(1000, 5000)
        timestamp_val = int(datetime.now().timestamp()) - random.randint(100, 500)
        
        sla_input = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp_val
                }
            }
        }
        
        result = track_incident_sla(sla_input)
        
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)
        self.assertIsInstance(result["time_remaining_seconds"], float)

    def test_track_incident_sla_without_timestamp(self):
        threshold = random.randint(1000, 5000)
        sla_input = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "data": {}
            }
        }
        
        result = track_incident_sla(sla_input)
        
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertFalse(result["breach_predicted"])
        self.assertEqual(result["time_remaining_seconds"], float(threshold))

    def test_pipeline_integration_mocked(self):
        with patch("skills.incident_sla_tracker.aggregate_incidents") as mock_agg, \
             patch("skills.incident_sla_tracker.evaluate_incident_severity") as mock_eval:

            mock_agg.return_value = {uuid.uuid4().hex: random.choice(["info", "error"])}
            mock_eval.return_value = {"severity": self.severity}

            created_at = datetime.now() - timedelta(seconds=random.randint(5, 50))
            self.tracker.register_incident(self.incident_id, self.severity, created_at)

            results = self.tracker.check_sla_breaches()
            self.assertIsInstance(results, list)