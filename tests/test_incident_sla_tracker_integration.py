import unittest
import uuid
import random
from datetime import datetime, timedelta
from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.incident_id = str(uuid.uuid4())
        self.severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        self.selected_severity = random.choice(self.severities)
        self.sla_thresholds = {
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 600
        }
        self.warning_threshold = 0.8
        self.tracker = IncidentSLATracker(self.sla_thresholds, self.warning_threshold)

    def test_real_incident_workflow_integration(self):
        creation_delta = random.randint(100, 5000)
        created_at = datetime.now() - timedelta(seconds=creation_delta)
        
        self.tracker.register_incident(
            incident_id=self.incident_id,
            severity=self.selected_severity,
            created_at=created_at
        )

        time_to_breach = self.tracker.get_time_to_breach(self.incident_id)
        self.assertIsInstance(time_to_breach, float)

        severity_result = evaluate_incident_severity({
            "incident_id": self.incident_id,
            "severity": self.selected_severity,
            "timestamp": created_at.timestamp()
        })
        self.assertIsNotNone(severity_result)

        aggregated = aggregate_incidents({
            "incident_id": self.incident_id,
            "data": {
                "severity": self.selected_severity,
                "timestamp": created_at.timestamp()
            }
        })
        self.assertIsInstance(aggregated, dict)

        sla_input = {
            "incident_id": self.incident_id,
            "aggregated_data": aggregated,
            "threshold_seconds": self.sla_thresholds[self.selected_severity]
        }

        tracking_result = track_incident_sla(sla_input)
        self.assertEqual(tracking_result["incident_id"], self.incident_id)
        self.assertIsInstance(tracking_result["breach_predicted"], bool)
        self.assertIsInstance(tracking_result["time_remaining_seconds"], float)

        breaches = self.tracker.check_sla_breaches(current_time=datetime.now())
        self.assertIsInstance(breaches, list)

        new_status = random.choice(["ACTIVE", "RESOLVED_VERIFIED", "WARNING"])
        self.tracker.update_incident_status(self.incident_id, new_status)
        
        with self.assertRaises(KeyError):
            self.tracker.get_time_to_breach(str(uuid.uuid4()))

if __name__ == "__main__":
    unittest.main()