import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity
from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla


class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_incident_sla_tracker_pipeline_integration(self):
        unique_incident_id = f"inc-{uuid.uuid4()}"
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severity_levels)

        raw_payload = {
            "id": unique_incident_id,
            "raw_text": f"System failure with code {random.randint(1000, 9999)}",
            "source": "integration_test_suite"
        }
        
        module_name = "test_module"
        exc = Exception("System failure")
        tb = "Traceback string"

        aggregated_result = aggregate_incidents(module_name, exc, tb)
        self.assertIsNotNone(aggregated_result)

        evaluation_result = evaluate_incident_severity(
            module_name=module_name,
            exception=exc,
            traceback_str=tb,
            incident_id=unique_incident_id
        )
        self.assertIsNotNone(evaluation_result)

        thresholds = {
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 600
        }
        
        tracker = IncidentSLATracker(
            sla_thresholds=thresholds,
            warning_threshold_pct=0.5
        )
        
        creation_time = datetime.now() - timedelta(seconds=random.randint(10, 100))
        tracker.register_incident(
            incident_id=unique_incident_id,
            severity=chosen_severity,
            created_at=creation_time
        )
        
        time_to_breach = tracker.get_time_to_breach(unique_incident_id)
        self.assertIsInstance(time_to_breach, float)

        sla_input = {
            "incident_id": unique_incident_id,
            "aggregated_data": {
                "data": {
                    "timestamp": creation_time.timestamp()
                }
            },
            "threshold_seconds": thresholds[chosen_severity]
        }
        
        tracked_output = track_incident_sla(sla_input)
        self.assertEqual(tracked_output["incident_id"], unique_incident_id)
        self.assertIn("breach_predicted", tracked_output)
        self.assertIn("time_remaining_seconds", tracked_output)

        breaches = tracker.check_sla_breaches()
        self.assertIsInstance(breaches, list)


if __name__ == "__main__":
    unittest.main()