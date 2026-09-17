import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_end_to_end_incident_sla_tracking(self):
        incident_id = f"inc-{uuid.uuid4()}"
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severities)
        
        severity_result = evaluate_incident_severity({"incident_id": incident_id, "level": chosen_severity})
        self.assertIsInstance(severity_result, dict)

        aggregated = aggregate_incidents({
            "incident_id": incident_id,
            "raw_data": {"severity": chosen_severity, "timestamp": datetime.now().timestamp()}
        })
        self.assertIsInstance(aggregated, dict)

        thresholds = {"LOW": 7200, "MEDIUM": 3600, "HIGH": 1800, "CRITICAL": 600}
        tracker = IncidentSLATracker(sla_thresholds=thresholds, warning_threshold_pct=0.8)
        
        past_time = datetime.now() - timedelta(seconds=random.randint(10, 100))
        tracker.register_incident(incident_id=incident_id, severity=chosen_severity, created_at=past_time)
        
        time_to_breach = tracker.get_time_to_breach(incident_id)
        self.assertIsInstance(time_to_breach, float)

        breaches = tracker.check_sla_breaches(current_time=datetime.now())
        self.assertIsInstance(breaches, list)

        sla_input = {
            "incident_id": incident_id,
            "aggregated_data": aggregated,
            "threshold_seconds": thresholds[chosen_severity]
        }
        tracking_result = track_incident_sla(sla_input)
        
        self.assertEqual(tracking_result["incident_id"], incident_id)
        self.assertIn("breach_predicted", tracking_result)
        self.assertIn("time_remaining_seconds", tracking_result)

if __name__ == "__main__":
    unittest.main()