import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_end_to_end_sla_tracking_pipeline(self):
        unique_id = f"INC-{uuid.uuid4().hex[:8]}"
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severity_levels)

        raw_severity_input = {
            "incident_id": unique_id,
            "metrics": {
                "error_rate": random.uniform(0.05, 0.95),
                "affected_users": random.randint(10, 5000)
            }
        }

        severity_result = evaluate_incident_severity(raw_severity_input)
        self.assertIsInstance(severity_result, dict)

        aggregation_input = {
            "incident_id": unique_id,
            "raw_data": {
                "timestamp": datetime.now().timestamp(),
                "source": "integration_test_suite"
            }
        }
        aggregated_data = aggregate_incidents(aggregation_input)
        self.assertIsInstance(aggregated_data, dict)

        thresholds = {
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 600
        }
        warning_pct = 0.5

        tracker = IncidentSLATracker(
            sla_thresholds=thresholds,
            warning_threshold_pct=warning_pct
        )

        past_creation_time = datetime.now() - timedelta(seconds=random.randint(100, 500))
        tracker.register_incident(
            incident_id=unique_id,
            severity=chosen_severity,
            created_at=past_creation_time
        )

        time_to_breach = tracker.get_time_to_breach(incident_id=unique_id)
        self.assertIsInstance(time_to_breach, float)

        sla_payload = {
            "incident_id": unique_id,
            "aggregated_data": aggregated_data,
            "threshold_seconds": thresholds.get(chosen_severity, 3600)
        }

        tracking_result = track_incident_sla(sla_payload)
        self.assertIsInstance(tracking_result, dict)
        self.assertEqual(tracking_result.get("incident_id"), unique_id)
        self.assertIn("breach_predicted", tracking_result)
        self.assertIn("time_remaining_seconds", tracking_result)

        breach_checks = tracker.check_sla_breaches()
        self.assertIsInstance(breach_checks, list)

        tracker.update_incident_status(incident_id=unique_id, status="RESOLVED")
        resolved_checks = tracker.check_sla_breaches()

        found_active_breach = any(item["incident_id"] == unique_id for item in resolved_checks)
        self.assertFalse(found_active_breach)

if __name__ == "__main__":
    unittest.main()