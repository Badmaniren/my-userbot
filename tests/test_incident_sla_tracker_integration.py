import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_sla_tracker_integration_flow(self):
        rand_suffix = str(uuid.uuid4())[:8]
        incident_id = f"INC-{rand_suffix}"

        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severities)
        
        eval_result = evaluate_incident_severity({
            "incident_id": incident_id,
            "severity_hint": chosen_severity
        })
        
        agg_data = aggregate_incidents({
            "incident_id": incident_id,
            "raw_severity": eval_result.get("severity", chosen_severity)
        })
        
        thresholds = {"LOW": 7200, "MEDIUM": 3600, "HIGH": 1800, "CRITICAL": 600}
        tracker = IncidentSLATracker(sla_thresholds=thresholds, warning_threshold_pct=0.8)
        
        created_time = datetime.now() - timedelta(seconds=random.randint(10, 500))
        tracker.register_incident(
            incident_id=incident_id,
            severity=eval_result.get("severity", chosen_severity),
            created_at=created_time
        )
        
        time_to_breach = tracker.get_time_to_breach(incident_id)
        self.assertIsInstance(time_to_breach, float)

        breach_checks = tracker.check_sla_breaches()
        self.assertIsInstance(breach_checks, list)

        payload = {
            "incident_id": incident_id,
            "aggregated_data": agg_data,
            "threshold_seconds": thresholds.get(chosen_severity, 3600)
        }
        tracking_result = track_incident_sla(payload)
        
        self.assertIn("incident_id", tracking_result)
        self.assertEqual(tracking_result["incident_id"], incident_id)
        self.assertIn("breach_predicted", tracking_result)
        self.assertIn("time_remaining_seconds", tracking_result)

if __name__ == "__main__":
    unittest.main()