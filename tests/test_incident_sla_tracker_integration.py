import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_end_to_end_sla_tracking_and_aggregation_workflow(self):
        unique_incident_id = f"INC-{uuid.uuid4()}"
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        selected_severity = random.choice(severity_levels)
        
        evaluated_severity = evaluate_incident_severity({
            "incident_id": unique_incident_id,
            "raw_severity": selected_severity
        })
        
        self.assertIsInstance(evaluated_severity, dict)

        creation_time = datetime.now() - timedelta(seconds=random.randint(10, 500))
        
        aggregated = aggregate_incidents({
            "incidents": [
                {
                    "incident_id": unique_incident_id,
                    "severity": selected_severity,
                    "timestamp": creation_time.timestamp()
                }
            ]
        })
        
        self.assertIsInstance(aggregated, dict)

        tracker = IncidentSLATracker(
            sla_thresholds={"LOW": 7200, "MEDIUM": 3600, "HIGH": 1800, "CRITICAL": 600},
            warning_threshold_pct=0.8
        )
        
        tracker.register_incident(
            incident_id=unique_incident_id,
            severity=selected_severity,
            created_at=creation_time
        )

        time_to_breach = tracker.get_time_to_breach(unique_incident_id)
        self.assertIsInstance(time_to_breach, float)

        breach_status_list = tracker.check_sla_breaches()
        self.assertIsInstance(breach_status_list, list)

        sla_input = {
            "incident_id": unique_incident_id,
            "threshold_seconds": 3600,
            "aggregated_data": {
                "incidents": [
                    {
                        "incident_id": unique_incident_id,
                        "data": {
                            "timestamp": creation_time.timestamp()
                        }
                    }
                ]
            }
        }

        result = track_incident_sla(sla_input)
        
        self.assertEqual(result["incident_id"], unique_incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)
        self.assertIsInstance(result["time_remaining_seconds"], float)

if __name__ == "__main__":
    unittest.main()