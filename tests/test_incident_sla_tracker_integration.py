import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_end_to_end_sla_workflow_without_mocks(self):
        rand_suffix = str(uuid.uuid4())[:8]
        incident_id = f"inc-{rand_suffix}"
        raw_log = f"CRITICAL system failure in module {rand_suffix}"

        severity_result = evaluate_incident_severity({"log": raw_log})
        self.assertIn("severity", severity_result)
        severity = severity_result["severity"]

        agg_result = aggregate_incidents([{"incident_id": incident_id, "log": raw_log, "severity": severity}])
        self.assertIsInstance(agg_result, dict)

        thresholds = {"CRITICAL": 10, "HIGH": 60, "MEDIUM": 120}
        tracker = IncidentSLATracker(sla_thresholds=thresholds, warning_threshold_pct=0.5)

        created_time = datetime.now() - timedelta(seconds=random.randint(1, 5))
        tracker.register_incident(incident_id=incident_id, severity=severity, created_at=created_time)

        time_to_breach = tracker.get_time_to_breach(incident_id)
        self.assertIsInstance(time_to_breach, float)

        breaches = tracker.check_sla_breaches(current_time=datetime.now())
        self.assertIsInstance(breaches, list)

        timestamp_epoch = created_time.timestamp()
        sla_input = {
            "incident_id": incident_id,
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp_epoch
                }
            },
            "threshold_seconds": thresholds.get(severity, 3600)
        }

        tracking_output = track_incident_sla(sla_input)
        self.assertEqual(tracking_output["incident_id"], incident_id)
        self.assertIn("breach_predicted", tracking_output)
        self.assertIn("time_remaining_seconds", tracking_output)

if __name__ == "__main__":
    unittest.main()