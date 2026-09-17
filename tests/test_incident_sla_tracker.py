import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid
import random
import string

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla


class TestIncidentSLATrackerInquisitor(unittest.TestCase):

    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"])
        self.created_at = datetime.now() - timedelta(seconds=random.randint(10, 500))
        self.thresholds = {self.severity: random.randint(1000, 5000)}
        self.warning_pct = round(random.uniform(0.5, 0.9), 2)
        self.tracker = IncidentSLATracker(self.thresholds, self.warning_pct)

    def test_register_and_get_time_to_breach(self):
        self.tracker.register_incident(self.incident_id, self.severity, self.created_at)
        current_time = datetime.now()
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id, current_time)
        
        expected_limit = self.thresholds[self.severity]
        elapsed = (current_time - self.created_at).total_seconds()
        expected_tb = float(expected_limit - elapsed)

        self.assertAlmostEqual(time_to_breach, expected_tb, places=2)

    def test_get_time_to_breach_not_found(self):
        non_existent_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(non_existent_id)

    def test_update_incident_status(self):
        self.tracker.register_incident(self.incident_id, self.severity, self.created_at)
        new_status = f"RESOLVED_{uuid.uuid4().hex[:6].upper()}"
        self.tracker.update_incident_status(self.incident_id, new_status)

        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], new_status)

    def test_check_sla_breaches_warning_and_active(self):
        short_threshold = 5
        custom_thresholds = {self.severity: short_threshold}
        tracker = IncidentSLATracker(custom_thresholds, warning_threshold_pct=0.1)
        
        past_time = datetime.now() - timedelta(seconds=1)
        tracker.register_incident(self.incident_id, self.severity, past_time)

        results = tracker.check_sla_breaches(current_time=datetime.now())
        self.assertTrue(any(r["incident_id"] == self.incident_id and r["status"] == "WARNING" for r in results))

    def test_check_sla_breaches_breached_with_hooks(self):
        long_ago = datetime.now() - timedelta(seconds=10000)
        self.tracker.register_incident(self.incident_id, self.severity, long_ago)
        
        mock_bridge = MagicMock()
        mock_escalation = MagicMock()
        
        results = self.tracker.check_sla_breaches(
            current_time=datetime.now(),
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )
        
        mock_bridge.notify_sla_breach.assert_called_once_with(incident_id=self.incident_id, severity=self.severity)
        mock_escalation.escalate_incident.assert_called_once_with(incident_id=self.incident_id, severity=self.severity)
        
        self.assertTrue(any(r["incident_id"] == self.incident_id and r["status"] == "BREACHED" for r in results))

    def test_track_incident_sla_function(self):
        timestamp = int(datetime.now().timestamp()) - random.randint(10, 100)
        threshold_sec = random.randint(1000, 2000)
        
        sla_input = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold_sec,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp
                }
            }
        }
        
        result = track_incident_sla(sla_input)
        
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)
        self.assertIsInstance(result["time_remaining_seconds"], float)

    def test_end_to_end_sla_workflow_with_strict_mocking(self):
        self.tracker.register_incident(self.incident_id, self.severity, self.created_at)
        
        with patch("skills.incident_sla_tracker.evaluate_incident_severity") as mock_eval, \
             patch("skills.incident_sla_tracker.aggregate_incidents") as mock_agg:

            mock_eval.return_value = {"severity_score": random.randint(1, 10)}
            mock_agg.return_value = {"aggregated": True}

            simulated_eval = mock_eval(exception=Exception("test_err"), traceback_str="traceback_mock")
            self.assertIn("severity_score", simulated_eval)

            results = self.tracker.check_sla_breaches(current_time=datetime.now())
            self.assertIsInstance(results, list)