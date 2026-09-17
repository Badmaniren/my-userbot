import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import random
import uuid

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_severity_evaluator import evaluate_incident_severity


class TestIncidentSLATracker(unittest.TestCase):

    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.sla_thresholds = {
            "LOW": random.randint(7200, 14400),
            "MEDIUM": random.randint(3600, 7199),
            "HIGH": random.randint(1800, 3599),
            "CRITICAL": random.randint(300, 1799)
        }
        self.warning_threshold_pct = round(random.uniform(0.5, 0.9), 2)
        self.tracker = IncidentSLATracker(
            sla_thresholds=self.sla_thresholds,
            warning_threshold_pct=self.warning_threshold_pct
        )

    def test_register_incident_and_time_to_breach(self):
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id)
        expected_limit = self.sla_thresholds[self.severity]
        
        self.assertIsInstance(time_to_breach, float)
        self.assertLess(time_to_breach, expected_limit)

    def test_get_time_to_breach_not_found(self):
        unknown_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(unknown_id)

    def test_update_incident_status(self):
        created_at = datetime.now()
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"
        self.tracker.update_incident_status(self.incident_id, new_status)

        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], new_status)

    def test_check_sla_breaches_warning(self):
        sla_limit = self.sla_thresholds[self.severity]
        warning_seconds = int(sla_limit * self.warning_threshold_pct) + random.randint(1, 10)
        created_at = datetime.now() - timedelta(seconds=warning_seconds)

        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        results = self.tracker.check_sla_breaches()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["incident_id"], self.incident_id)
        self.assertEqual(results[0]["status"], "WARNING")

    def test_check_sla_breaches_breached_with_bridges(self):
        sla_limit = self.sla_thresholds[self.severity]
        breach_seconds = sla_limit + random.randint(10, 100)
        created_at = datetime.now() - timedelta(seconds=breach_seconds)
        
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        mock_notification = MagicMock()
        mock_escalation = MagicMock()
        
        results = self.tracker.check_sla_breaches(
            notification_bridge=mock_notification,
            escalation_engine=mock_escalation
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "BREACHED")
        mock_notification.notify_sla_breach.assert_called_once_with(
            incident_id=self.incident_id, severity=self.severity
        )
        mock_escalation.escalate_incident.assert_called_once_with(
            incident_id=self.incident_id, severity=self.severity
        )

    def test_track_incident_sla_function(self):
        threshold = random.randint(1000, 5000)
        timestamp = int(datetime.now().timestamp()) - random.randint(100, 500)
        sla_input = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold,
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


class TestIncidentSLATrackerIntegration(unittest.TestCase):

    def test_end_to_end_sla_tracking_and_aggregation(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        with patch("skills.incident_severity_evaluator.evaluate_incident_severity") as mock_eval:
            mock_eval.return_value = {"severity": severity, "score": random.randint(1, 10)}

            evaluated_severity = evaluate_incident_severity(
                exception=Exception(uuid.uuid4().hex),
                traceback_str=uuid.uuid4().hex
            )

            sla_thresholds = {evaluated_severity["severity"]: random.randint(100, 1000)}
            tracker = IncidentSLATracker(sla_thresholds=sla_thresholds, warning_threshold_pct=0.8)

            created_at = datetime.now() - timedelta(seconds=2000)
            tracker.register_incident(incident_id, evaluated_severity["severity"], created_at)

            results = tracker.check_sla_breaches()
            self.assertTrue(len(results) > 0)
            self.assertEqual(results[0]["incident_id"], incident_id)


if __name__ == "__main__":
    unittest.main()