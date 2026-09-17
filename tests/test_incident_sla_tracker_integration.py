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

        raw_payload = {
            "incident_id": unique_incident_id,
            "raw_log": f"System failure detected with code {random.randint(1000, 9999)}"
        }

        aggregated = aggregate_incidents(raw_payload)
        self.assertIsInstance(aggregated, dict)

        evaluated_severity = evaluate_incident_severity({
            "incident_id": unique_incident_id,
            "severity_hint": chosen_severity,
            "aggregated_metrics": aggregated
        })
        self.assertIsInstance(evaluated_severity, dict)

        sla_thresholds = {
            "LOW": 86400,
            "MEDIUM": 14400,
            "HIGH": 3600,
            "CRITICAL": 600
        }
        warning_pct = 0.8

        tracker = IncidentSLATracker(sla_thresholds=sla_thresholds, warning_threshold_pct=warning_pct)
        
        created_time = datetime.now() - timedelta(seconds=random.randint(10, 500))
        tracker.register_incident(
            incident_id=unique_incident_id,
            severity=chosen_severity,
            created_at=created_time
        )

        time_to_breach = tracker.get_time_to_breach(unique_incident_id)
        self.assertIsInstance(time_to_breach, float)

        current_timestamp = int(created_time.timestamp())
        sla_input = {
            "incident_id": unique_incident_id,
            "aggregated_data": {
                "data": {
                    "timestamp": current_timestamp
                }
            },
            "threshold_seconds": sla_thresholds[chosen_severity]
        }

        tracking_result = track_incident_sla(sla_input)
        self.assertIsInstance(tracking_result, dict)
        self.assertEqual(tracking_result.get("incident_id"), unique_incident_id)
        self.assertIn("breach_predicted", tracking_result)
        self.assertIn("time_remaining_seconds", tracking_result)

        breach_checks = tracker.check_sla_breaches()
        self.assertIsInstance(breach_checks, list)


if __name__ == "__main__":
    unittest.main()