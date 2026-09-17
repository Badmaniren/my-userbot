import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity
from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla


class TestIncidentSLATrackerIntegration(unittest.TestCase):

    def test_incident_sla_tracker_integration_workflow(self):
        unique_incident_id = f"inc-{uuid.uuid4()}"
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severities)

        raw_timestamp = datetime.now() - timedelta(seconds=random.randint(10, 500))
        
        aggregated = aggregate_incidents({
            "incident_id": unique_incident_id,
            "raw_data": {
                "severity": chosen_severity,
                "timestamp": raw_timestamp.timestamp()
            }
        })

        evaluated_severity = evaluate_incident_severity({
            "incident_id": unique_incident_id,
            "severity": chosen_severity
        })

        self.assertIsNotNone(aggregated)
        self.assertIsNotNone(evaluated_severity)

        sla_thresholds = {
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 600
        }
        warning_pct = 0.8

        tracker = IncidentSLATracker(sla_thresholds=sla_thresholds, warning_threshold_pct=warning_pct)
        
        tracker.register_incident(
            incident_id=unique_incident_id,
            severity=evaluated_severity.get("severity", chosen_severity),
            created_at=raw_timestamp
        )

        time_to_breach = tracker.get_time_to_breach(unique_incident_id)
        self.assertIsInstance(time_to_breach, float)

        breach_checks = tracker.check_sla_breaches(current_time=datetime.now())
        self.assertIsInstance(breach_checks, list)

        payload = {
            "incident_id": unique_incident_id,
            "aggregated_data": {
                "data": {
                    "timestamp": raw_timestamp.timestamp()
                }
            },
            "threshold_seconds": sla_thresholds.get(chosen_severity, 3600)
        }

        result = track_incident_sla(payload)

        self.assertIn("incident_id", result)
        self.assertEqual(result["incident_id"], unique_incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)
        self.assertIsInstance(result["time_remaining_seconds"], float)


if __name__ == "__main__":
    unittest.main()