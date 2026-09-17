import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_sla_tracker_full_integration(self):
        inc_id = str(uuid.uuid4())
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severities)

        severity_result = evaluate_incident_severity({"incident_id": inc_id, "severity_hint": chosen_severity})
        self.assertIsInstance(severity_result, dict)

        timestamp_val = datetime.now().timestamp() - random.randint(10, 100)
        agg_input = {
            "incident_id": inc_id,
            "raw_data": {
                "timestamp": timestamp_val,
                "severity": chosen_severity
            }
        }
        aggregated = aggregate_incidents(agg_input)
        self.assertIsInstance(aggregated, dict)

        thresholds = {"LOW": 7200, "MEDIUM": 3600, "HIGH": 1800, "CRITICAL": 600}
        tracker = IncidentSLATracker(sla_thresholds=thresholds, warning_threshold_pct=0.5)

        created_time = datetime.fromtimestamp(timestamp_val)
        tracker.register_incident(incident_id=inc_id, severity=chosen_severity, created_at=created_time)

        time_to_breach = tracker.get_time_to_breach(incident_id=inc_id)
        self.assertIsInstance(time_to_breach, float)

        breach_results = tracker.check_sla_breaches(current_time=datetime.now())
        self.assertIsInstance(breach_results, list)

        sla_input = {
            "incident_id": inc_id,
            "aggregated_data": aggregated,
            "threshold_seconds": thresholds[chosen_severity]
        }
        tracking_result = track_incident_sla(sla_input)

        self.assertIsInstance(tracking_result, dict)
        self.assertEqual(tracking_result.get("incident_id"), inc_id)
        self.assertIn("breach_predicted", tracking_result)
        self.assertIn("time_remaining_seconds", tracking_result)

if __name__ == "__main__":
    unittest.main()