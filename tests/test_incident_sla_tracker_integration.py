import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity
from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_end_to_end_sla_tracker_integration(self):
        unique_incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severities)
        
        severity_eval_input = {
            "incident_id": unique_incident_id,
            "raw_severity": chosen_severity
        }
        evaluated_severity_result = evaluate_incident_severity(severity_eval_input)
        effective_severity = evaluated_severity_result.get("severity", chosen_severity)

        raw_timestamp = datetime.now() - timedelta(seconds=random.randint(100, 5000))
        aggregator_input = {
            "incident_id": unique_incident_id,
            "data": {
                "timestamp": raw_timestamp.timestamp(),
                "severity": effective_severity
            }
        }
        aggregated_result = aggregate_incidents(aggregator_input)

        thresholds = {
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 600
        }
        tracker = IncidentSLATracker(sla_thresholds=thresholds, warning_threshold_pct=0.8)
        
        tracker.register_incident(
            incident_id=unique_incident_id,
            severity=effective_severity,
            created_at=raw_timestamp
        )

        time_to_breach = tracker.get_time_to_breach(unique_incident_id)
        self.assertIsInstance(time_to_breach, float)

        breach_checks = tracker.check_sla_breaches()
        self.assertIsInstance(breach_checks, list)

        sla_input = {
            "incident_id": unique_incident_id,
            "aggregated_data": aggregated_result,
            "threshold_seconds": thresholds.get(effective_severity, 3600)
        }
        tracking_result = track_incident_sla(sla_input)

        self.assertEqual(tracking_result["incident_id"], unique_incident_id)
        self.assertIn("breach_predicted", tracking_result)
        self.assertIn("time_remaining_seconds", tracking_result)

        tracker.update_incident_status(unique_incident_id, "RESOLVED")
        resolved_checks = tracker.check_sla_breaches()

        resolved_found = any(item["incident_id"] == unique_incident_id for item in resolved_checks)
        self.assertFalse(resolved_found)

if __name__ == "__main__":
    unittest.main()