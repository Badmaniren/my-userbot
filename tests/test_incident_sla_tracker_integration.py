import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_end_to_end_sla_workflow(self):
        unique_id = f"inc-{uuid.uuid4()}"
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severity_levels)
        
        severity_result = evaluate_incident_severity({
            "incident_id": unique_id,
            "severity": chosen_severity
        })
        self.assertIsInstance(severity_result, dict)

        aggregated = aggregate_incidents({
            "incident_id": unique_id,
            "data": {
                "timestamp": datetime.now().timestamp(),
                "severity": chosen_severity
            }
        })
        self.assertIsInstance(aggregated, dict)

        tracker = IncidentSLATracker(
            sla_thresholds={"LOW": 7200, "MEDIUM": 3600, "HIGH": 1800, "CRITICAL": 600},
            warning_threshold_pct=0.8
        )
        
        past_time = datetime.now() - timedelta(seconds=random.randint(100, 5000))
        tracker.register_incident(unique_id, chosen_severity, past_time)

        time_to_breach = tracker.get_time_to_breach(unique_id)
        self.assertIsInstance(time_to_breach, float)

        breaches = tracker.check_sla_breaches()
        self.assertIsInstance(breaches, list)

        sla_input = {
            "incident_id": unique_id,
            "aggregated_data": aggregated,
            "threshold_seconds": 3600
        }
        track_result = track_incident_sla(sla_input)
        
        self.assertEqual(track_result["incident_id"], unique_id)
        self.assertIn("breach_predicted", track_result)
        self.assertIn("time_remaining_seconds", track_result)

if __name__ == "__main__":
    unittest.main()