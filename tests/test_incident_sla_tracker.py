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
        self.sla_thresholds = {
            "LOW": random.randint(7200, 14400),
            "MEDIUM": random.randint(3600, 7199),
            "HIGH": random.randint(1800, 3599),
            "CRITICAL": random.randint(60, 1799)
        }
        self.warning_threshold_pct = round(random.uniform(0.5, 0.9), 2)
        self.tracker = IncidentSLATracker(self.sla_thresholds, self.warning_threshold_pct)

    def test_register_incident(self):
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        self.assertIn(self.incident_id, self.tracker.incidents)
        incident_data = self.tracker.incidents[self.incident_id]
        self.assertEqual(incident_data["severity"], self.severity)
        self.assertEqual(incident_data["created_at"], created_at)
        self.assertEqual(incident_data["status"], "ACTIVE")

    def test_get_time_to_breach_success(self):
        delta_seconds = random.randint(100, 500)
        created_at = datetime.now() - timedelta(seconds=delta_seconds)
        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        current_time = datetime.now()
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id, current_time)
        
        expected_sla = self.sla_thresholds.get(self.severity, 3600)
        expected_remaining = expected_sla - delta_seconds
        self.assertAlmostEqual(time_to_breach, expected_remaining, delta=2.0)

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
        sla_limit = self.sla_thresholds[self.severity]
        elapsed_seconds = int(sla_limit * self.warning_threshold_pct) + random.randint(1, 10)
        created_at = datetime.now() - timedelta(seconds=elapsed_seconds)
        
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        results = self.tracker.check_sla_breaches(current_time=datetime.now())
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["incident_id"], self.incident_id)
        self.assertEqual(results[0]["status"], "WARNING")

    def test_check_sla_breaches_breached(self):
        sla_limit = self.sla_thresholds[self.severity]
        elapsed_seconds = sla_limit + random.randint(10, 100)
        created_at = datetime.now() - timedelta(seconds=elapsed_seconds)

        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        mock_bridge = MagicMock()
        mock_escalation = MagicMock()
        
        results = self.tracker.check_sla_breaches(
            current_time=datetime.now(),
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["incident_id"], self.incident_id)
        self.assertEqual(results[0]["status"], "BREACHED")

        mock_bridge.notify_sla_breach.assert_called_once_with(
            incident_id=self.incident_id, severity=self.severity
        )
        mock_escalation.escalate_incident.assert_called_once_with(
            incident_id=self.incident_id, severity=self.severity
        )

    def test_check_sla_breaches_resolved_skipped(self):
        sla_limit = self.sla_thresholds[self.severity]
        elapsed_seconds = sla_limit + random.randint(100, 200)
        created_at = datetime.now() - timedelta(seconds=elapsed_seconds)

        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        self.tracker.update_incident_status(self.incident_id, "RESOLVED_SUCCESSFULLY")
        
        results = self.tracker.check_sla_breaches(current_time=datetime.now())
        self.assertEqual(len(results), 0)

    def test_track_incident_sla_function_with_timestamp(self):
        timestamp = int(datetime.now().timestamp()) - random.randint(50, 200)
        threshold = random.randint(1000, 5000)
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
        self.assertIsInstance(result["breach_predicted"], bool)
        self.assertIsInstance(result["time_remaining_seconds"], float)

    def test_track_incident_sla_function_without_timestamp(self):
        threshold = random.randint(1000, 5000)
        sla_input = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {}
        }
        
        result = track_incident_sla(sla_input)
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)


class TestIncidentSLATrackerIntegration(unittest.TestCase):

    def test_end_to_end_sla_tracking_and_aggregation(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        threshold = random.randint(1000, 5000)
        
        with patch("skills.incident_aggregator.aggregate_incidents") as mock_aggregate, \
             patch("skills.incident_severity_evaluator.evaluate_incident_severity") as mock_evaluate:
            
            mock_aggregate.return_value = {
                "status": "ok",
                "incident_id": incident_id,
                "data": {"timestamp": int(datetime.now().timestamp())}
            }
            mock_evaluate.return_value = {
                "severity": severity,
                "score": random.random()
            }

            aggregated = mock_aggregate(incident_id)
            evaluated = mock_evaluate(Exception("test_error"), "traceback_string")

            self.assertEqual(aggregated["incident_id"], incident_id)
            self.assertEqual(evaluated["severity"], severity)

            sla_input = {
                "incident_id": incident_id,
                "threshold_seconds": threshold,
                "aggregated_data": aggregated
            }

            result = track_incident_sla(sla_input)
            self.assertEqual(result["incident_id"], incident_id)
            self.assertIsInstance(result["breach_predicted"], bool)


if __name__ == "__main__":
    unittest.main()