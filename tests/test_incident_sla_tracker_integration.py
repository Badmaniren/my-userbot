import unittest
from datetime import datetime, timedelta
import uuid
import random

from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity
from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla


class TestIncidentSLATrackerIntegration(unittest.TestCase):

    def setUp(self):
        self.incident_id = f"inc-{uuid.uuid4()}"
        self.severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        self.selected_severity = random.choice(self.severity_levels)

        self.sla_thresholds = {
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 600
        }
        self.warning_pct = 0.8
        
        self.tracker = IncidentSLATracker(
            sla_thresholds=self.sla_thresholds,
            warning_threshold_pct=self.warning_pct
        )

    def test_end_to_end_sla_lifecycle(self):
        created_time = datetime.now() - timedelta(seconds=random.randint(100, 500))

        self.tracker.register_incident(
            incident_id=self.incident_id,
            severity=self.selected_severity,
            created_at=created_time
        )

        time_to_breach = self.tracker.get_time_to_breach(self.incident_id)
        self.assertIsInstance(time_to_breach, float)

        future_breach_time = created_time + timedelta(seconds=self.sla_thresholds[self.selected_severity] + 100)
        breach_check_results = self.tracker.check_sla_breaches(current_time=future_breach_time)

        found_breach = False
        for result in breach_check_results:
            if result["incident_id"] == self.incident_id:
                self.assertEqual(result["status"], "BREACHED")
                found_breach = True
                break
        self.assertTrue(found_breach, f"Incident {self.incident_id} should have breached SLA.")

    def test_functional_track_incident_sla_wrapper(self):
        timestamp_val = int(datetime.now().timestamp()) - random.randint(50, 200)
        threshold_val = random.choice([1000, 2000, 3600])

        payload = {
            "incident_id": self.incident_id,
            "threshold_seconds": threshold_val,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp_val
                }
            }
        }

        result = track_incident_sla(payload)

        self.assertIn("incident_id", result)
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)
        self.assertIsInstance(result["breach_predicted"], bool)
        self.assertIsInstance(result["time_remaining_seconds"], float)


if __name__ == "__main__":
    unittest.main()