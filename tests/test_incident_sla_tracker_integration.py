import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_end_to_end_sla_workflow(self):
        unique_incident_id = f"inc-{uuid.uuid4()}"
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severities)
        
        evaluated_severity = evaluate_incident_severity({
            "incident_id": unique_incident_id,
            "raw_severity": chosen_severity
        })
        
        self.assertIsNotNone(evaluated_severity)

        aggregated = aggregate_incidents({
            "incident_id": unique_incident_id,
            "severity": chosen_severity,
            "data": {
                "timestamp": datetime.now().timestamp() - random.randint(10, 100)
            }
        })
        
        self.assertIsInstance(aggregated, dict)

        tracker = IncidentSLATracker(
            sla_thresholds={"LOW": 7200, "MEDIUM": 3600, "HIGH": 1800, "CRITICAL": 600},
            warning_threshold_pct=0.8
        )

        created_time = datetime.now() - timedelta(seconds=random.randint(500, 1000))
        tracker.register_incident(
            incident_id=unique_incident_id,
            severity=chosen_severity,
            created_at=created_time
        )

        time_to_breach = tracker.get_time_to_breach(unique_incident_id)
        self.assertIsInstance(time_to_breach, float)

        breaches = tracker.check_sla_breaches(current_time=datetime.now())
        self.assertIsInstance(breaches, list)

        sla_input_payload = {
            "incident_id": unique_incident_id,
            "aggregated_data": aggregated,
            "threshold_seconds": 3600
        }
        
        result = track_incident_sla(sla_input_payload)
        self.assertEqual(result["incident_id"], unique_incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)

if __name__ == "__main__":
    unittest.main()