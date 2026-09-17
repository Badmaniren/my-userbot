import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import random
import uuid

from skills.incident_sla_tracker import (
    IncidentSLATracker,
    track_incident_sla
)

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
        self.tracker.register_incident(
            incident_id=self.incident_id,
            severity=self.severity,
            created_at=created_at
        )
        
        self.assertIn(self.incident_id, self.tracker.incidents)
        incident_data = self.tracker.incidents[self.incident_id]
        self.assertEqual(incident_data["severity"], self.severity)
        self.assertEqual(incident_data["status"], "ACTIVE")
        
        time_to_breach = self.tracker.get_time_to_breach(self.incident_id)
        self.assertIsInstance(time_to_breach, float)

    def test_get_time_to_breach_nonexistent(self):
        fake_id = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(fake_id)

    def test_update_incident_status(self):
        created_at = datetime.now()
        self.tracker.register_incident(
            incident_id=self.incident_id,
            severity=self.severity,
            created_at=created_at
        )

        new_status = f"RESOLVED_{uuid.uuid4().hex[:6]}"
        self.tracker.update_incident_status(self.incident_id, new_status)
        self.assertEqual(self.tracker.incidents[self.incident_id]["status"], new_status)

    def test_check_sla_breaches_warning_and_breach(self):
        now = datetime.now()
        limit = self.sla_thresholds[self.severity]
        
        warning_id = uuid.uuid4().hex
        warning_created = now - timedelta(seconds=int(limit * self.warning_threshold_pct))
        self.tracker.register_incident(warning_id, self.severity, warning_created)
        
        breach_id = uuid.uuid4().hex
        breach_created = now - timedelta(seconds=limit + random.randint(10, 500))
        self.tracker.register_incident(breach_id, self.severity, breach_created)

        mock_notification = MagicMock()
        mock_escalation = MagicMock()
        
        results = self.tracker.check_sla_breaches(
            current_time=now,
            notification_bridge=mock_notification,
            escalation_engine=mock_escalation
        )
        
        result_ids = [r["incident_id"] for r in results]
        self.assertIn(warning_id, result_ids)
        self.assertIn(breach_id, result_ids)
        
        mock_notification.notify_sla_breach.assert_called_once()
        mock_escalation.escalate_incident.assert_called_once()

    def test_check_sla_breaches_resolved_ignored(self):
        now = datetime.now()
        limit = self.sla_thresholds[self.severity]
        breach_created = now - timedelta(seconds=limit + 100)
        
        self.tracker.register_incident(self.incident_id, self.severity, breach_created)
        self.tracker.update_incident_status(self.incident_id, "RESOLVED")
        
        results = self.tracker.check_sla_breaches(current_time=now)
        self.assertEqual(len(results), 0)

    def test_track_incident_sla_function(self):
        threshold = random.randint(1000, 5000)
        payload = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": {
                "incidents": [
                    {
                        "data": {
                            "timestamp": int(datetime.now().timestamp()) - 100
                        }
                    }
                ]
            }
        }
        
        res = track_incident_sla(payload)
        self.assertEqual(res["incident_id"], self.incident_id)
        self.assertIn("breach_predicted", res)
        self.assertIn("time_remaining_seconds", res)

    def test_end_to_end_sla_tracker_integration(self):
        with patch("skills.incident_aggregator.aggregate_incidents") as mock_agg, \
             patch("skills.incident_severity_evaluator.evaluate_incident_severity") as mock_eval:

            mock_agg.return_value = {uuid.uuid4().hex: random.choice(["INFO", "ERROR"])}
            mock_eval.return_value = {"severity": self.severity}

            created_at = datetime.now() - timedelta(seconds=random.randint(5, 50))
            self.tracker.register_incident(self.incident_id, self.severity, created_at)

            time_remaining = self.tracker.get_time_to_breach(self.incident_id)
            self.assertIsInstance(time_remaining, float)

            results = self.tracker.check_sla_breaches()
            self.assertIsInstance(results, list)

if __name__ == "__main__":
    unittest.main()