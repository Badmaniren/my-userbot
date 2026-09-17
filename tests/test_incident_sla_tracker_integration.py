import unittest
import uuid
import random
from datetime import datetime, timezone, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity


class TestIncidentSLATrackerIntegration(unittest.TestCase):

    def test_end_to_end_sla_workflow(self):
        inc_id = f"inc-{uuid.uuid4()}"
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severity_levels)

        severity_result = evaluate_incident_severity({"incident_id": inc_id, "severity": chosen_severity})
        self.assertIn("severity", severity_result)

        raw_timestamp = datetime.now(timezone.utc) - timedelta(seconds=random.randint(10, 500))
        aggregated = aggregate_incidents({
            "incident_id": inc_id,
            "data": {
                "timestamp": raw_timestamp.timestamp(),
                "severity": chosen_severity
            }
        })
        self.assertIn("incident_id", aggregated)

        thresholds = {"LOW": 7200, "MEDIUM": 3600, "HIGH": 1800, "CRITICAL": 600}
        tracker = IncidentSLATracker(sla_thresholds=thresholds, warning_threshold_pct=0.8)

        tracker.register_incident(inc_id, chosen_severity, raw_timestamp)

        time_to_breach = tracker.get_time_to_breach(inc_id, current_time=datetime.now(timezone.utc))
        self.assertIsInstance(time_to_breach, float)

        sla_input = {
            "incident_id": inc_id,
            "aggregated_data": aggregated,
            "threshold_seconds": thresholds[chosen_severity]
        }
        tracked_result = track_incident_sla(sla_input)

        self.assertEqual(tracked_result["incident_id"], inc_id)
        self.assertIsInstance(tracked_result["breach_predicted"], bool)
        self.assertIsInstance(tracked_result["time_remaining_seconds"], float)

        breaches = tracker.check_sla_breaches(current_time=datetime.now(timezone.utc))
        self.assertIsInstance(breaches, list)


if __name__ == "__main__":
    unittest.main()