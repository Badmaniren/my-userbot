import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_sla_tracker_full_integration(self):
        incident_id = f"inc-{uuid.uuid4()}"
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severities)
        
        severity_result = evaluate_incident_severity({"incident_id": incident_id, "raw_severity": chosen_severity})
        self.assertIsInstance(severity_result, dict)

        aggregated = aggregate_incidents([{"incident_id": incident_id, "severity": chosen_severity}])
        self.assertIsInstance(aggregated, dict)

        thresholds = {"LOW": 7200, "MEDIUM": 3600, "HIGH": 1800, "CRITICAL": 600}
        tracker = IncidentSLATracker(sla_thresholds=thresholds, warning_threshold_pct=0.8)

        created_time = datetime.now() - timedelta(seconds=random.randint(100, 5000))
        tracker.register_incident(incident_id=incident_id, severity=chosen_severity, created_at=created_time)

        time_to_breach = tracker.get_time_to_breach(incident_id)
        self.assertIsInstance(time_to_breach, float)

        breaches = tracker.check_sla_breaches(current_time=datetime.now())
        self.assertIsInstance(breaches, list)

        payload = {
            "incident_id": incident_id,
            "aggregated_data": {
                "data": {
                    "timestamp": created_time.timestamp()
                }
            },
            "threshold_seconds": thresholds[chosen_severity]
        }

        tracking_result = track_incident_sla(payload)
        self.assertEqual(tracking_result["incident_id"], incident_id)
        self.assertIsInstance(tracking_result["breach_predicted"], bool)
        self.assertIsInstance(tracking_result["time_remaining_seconds"], float)

if __name__ == "__main__":
    unittest.main()