import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import random
import uuid

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
        self.warning_pct = round(random.uniform(0.5, 0.8), 2)
        self.tracker = IncidentSLATracker(self.thresholds, self.warning_pct)

    def test_register_and_get_time_to_breach(self):
        created_at = datetime.now() - timedelta(seconds=random.randint(10, 100))
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        current_time = datetime.now()
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id, current_time)

        expected_limit = self.thresholds.get(self.severity, 3600)
        elapsed = (current_time - created_at).total_seconds()
        expected_ttb = float(expected_limit - elapsed)
        
        self.assertAlmostEqual(time_to_breach, expected_ttb, delta=1.0)

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
        sla_limit = self.thresholds[self.severity]
        elapsed_for_warning = int(sla_limit * self.warning_pct) + random.randint(1, 10)
        created_at = datetime.now() - timedelta(seconds=elapsed_for_warning)

        self.tracker.register_incident(self.incident_id, self.severity, created_at)

        results = self.tracker.check_sla_breaches(current_time=datetime.now())

        self.assertTrue(any(r["incident_id"] == self.incident_id and r["status"] == "WARNING" for r in results))

    def test_check_sla_breaches_breached_with_bridges(self):
        sla_limit = self.thresholds[self.severity]
        elapsed_for_breach = sla_limit + random.randint(10, 100)
        created_at = datetime.now() - timedelta(seconds=elapsed_for_breach)
        
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        
        mock_bridge = MagicMock()
        mock_escalation = MagicMock()
        
        results = self.tracker.check_sla_breaches(
            current_time=datetime.now(),
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )
        
        self.assertTrue(any(r["incident_id"] == self.incident_id and r["status"] == "BREACHED" for r in results))
        mock_bridge.notify_sla_breach.assert_called_once_with(incident_id=self.incident_id, severity=self.severity)
        mock_escalation.escalate_incident.assert_called_once_with(incident_id=self.incident_id, severity=self.severity)

    def test_check_sla_breaches_resolved_ignored(self):
        created_at = datetime.now() - timedelta(seconds=self.thresholds[self.severity] * 2)
        self.tracker.register_incident(self.incident_id, self.severity, created_at)
        self.tracker.update_incident_status(self.incident_id, "RESOLVED_COMPLETED")
        
        results = self.tracker.check_sla_breaches()
        self.assertNotIn(self.incident_id, [r["incident_id"] for r in results])

    def test_track_incident_sla_standalone(self):
        timestamp = int(datetime.now().timestamp()) - random.randint(50, 500)
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

    def test_integration_with_aggregator_and_evaluator_mocks(self):
        with patch("skills.incident_aggregator.aggregate_incidents") as mock_aggregator, \
             patch("skills.incident_severity_evaluator.evaluate_incident_severity") as mock_evaluator:

            mock_aggregator.return_value = {"status": "aggregated", "items": [self.incident_id]}
            mock_evaluator.return_value = {"severity_level": self.severity, "score": random.random()}

            agg_result = mock_aggregator()
            eval_result = mock_evaluator(exception=Exception(uuid.uuid4().hex), traceback_str=uuid.uuid4().hex)

            self.assertEqual(agg_result["status"], "aggregated")
            self.assertEqual(eval_result["severity_level"], self.severity)

            created_at = datetime.now()
            self.tracker.register_incident(self.incident_id, eval_result["severity_level"], created_at)
            ttb = self.tracker.get_time_to_breach(self.incident_id)
            self.assertIsInstance(ttb, float)

if __name__ == "__main__":
    unittest.main()