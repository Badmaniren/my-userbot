import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla

try:
    from skills.incident_aggregator import aggregate_incidents
except ImportError:
    aggregate_incidents = None

try:
    from skills.incident_severity_evaluator import evaluate_incident_severity
except ImportError:
    evaluate_incident_severity = None


class TestIncidentSLATrackerIntegration(unittest.TestCase):

    def test_sla_tracker_pipeline_integration(self):
        unique_incident_id = f"inc-{uuid.uuid4()}"
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severities)
        
        thresholds = {
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 600
        }
        
        warning_pct = 0.8
        tracker = IncidentSLATracker(sla_thresholds=thresholds, warning_threshold_pct=warning_pct)
        
        past_offset_seconds = random.randint(100, 5000)
        created_time = datetime.now() - timedelta(seconds=past_offset_seconds)
        
        tracker.register_incident(
            incident_id=unique_incident_id,
            severity=chosen_severity,
            created_at=created_time
        )
        
        time_to_breach = tracker.get_time_to_breach(unique_incident_id)
        self.assertIsInstance(time_to_breach, float)

        breach_results = tracker.check_sla_breaches()
        self.assertIsInstance(breach_results, list)

        timestamp_val = int(created_time.timestamp())
        random_payload = {
            "incident_id": unique_incident_id,
            "threshold_seconds": thresholds[chosen_severity],
            "aggregated_data": {
                "data": {
                    "timestamp": timestamp_val,
                    "severity": chosen_severity
                }
            }
        }

        if aggregate_incidents is not None:
            try:
                aggregate_incidents([random_payload])
            except Exception:
                pass

        if evaluate_incident_severity is not None:
            try:
                evaluate_incident_severity(unique_incident_id)
            except Exception:
                pass

        tracking_output = track_incident_sla(random_payload)
        
        self.assertIn("incident_id", tracking_output)
        self.assertEqual(tracking_output["incident_id"], unique_incident_id)
        self.assertIn("breach_predicted", tracking_output)
        self.assertIn("time_remaining_seconds", tracking_output)
        self.assertIsInstance(tracking_output["breach_predicted"], bool)
        self.assertIsInstance(tracking_output["time_remaining_seconds"], float)


if __name__ == "__main__":
    unittest.main()