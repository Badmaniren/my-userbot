import unittest
from datetime import datetime, timedelta
import uuid
import random

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity


class TestIncidentSLATrackerIntegration(unittest.TestCase):

    def test_end_to_end_sla_workflow(self):
        unique_id = f"inc-{uuid.uuid4()}"
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severities)

        severity_result = evaluate_incident_severity({"severity": chosen_severity})
        self.assertIsNotNone(severity_result)

        timestamp_val = datetime.now().timestamp() - random.randint(10, 100)
        raw_payload = {
            "incident_id": unique_id,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp_val,
                    "severity": chosen_severity
                }
            },
            "threshold_seconds": 60
        }

        aggregated = aggregate_incidents([raw_payload])
        self.assertIsInstance(aggregated, (dict, list))

        tracker = IncidentSLATracker(
            sla_thresholds={"LOW": 300, "MEDIUM": 120, "HIGH": 60, "CRITICAL": 30},
            warning_threshold_pct=0.5
        )

        created_time = datetime.now() - timedelta(seconds=random.randint(150, 310))
        tracker.register_incident(unique_id, chosen_severity, created_time)

        time_to_breach = tracker.get_time_to_breach(unique_id)
        self.assertIsInstance(time_to_breach, float)

        breaches = tracker.check_sla_breaches(current_time=datetime.now())
        found = any(b["incident_id"] == unique_id for b in breaches)
        self.assertTrue(found)

        track_result = track_incident_sla(raw_payload)
        self.assertEqual(track_result["incident_id"], unique_id)
        self.assertIn("breach_predicted", track_result)
        self.assertIn("time_remaining_seconds", track_result)


if __name__ == "__main__":
    unittest.main()