import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity
from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla


class RealIntegrationTestIncidentSLATracker(unittest.TestCase):

    def test_end_to_end_sla_tracker_pipeline(self):
        unique_incident_id = f"INC-{uuid.uuid4().hex[:8]}"
        random_severity = random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"])

        evaluated_severity = evaluate_incident_severity({
            "incident_id": unique_incident_id,
            "severity_level": random_severity
        })

        self.assertIsNotNone(evaluated_severity)

        past_timestamp = datetime.now() - timedelta(seconds=120)
        aggregated = aggregate_incidents({
            "incident_id": unique_incident_id,
            "data": {
                "timestamp": past_timestamp.timestamp(),
                "severity": random_severity
            }
        })

        self.assertIn("incident_id", aggregated)

        tracker = IncidentSLATracker(
            sla_thresholds={"CRITICAL": 60, "HIGH": 300, "MEDIUM": 600, "LOW": 3600},
            warning_threshold_pct=0.5
        )

        tracker.register_incident(
            incident_id=unique_incident_id,
            severity=random_severity,
            created_at=past_timestamp
        )

        time_to_breach = tracker.get_time_to_breach(unique_incident_id)
        self.assertIsInstance(time_to_breach, float)

        breaches = tracker.check_sla_breaches()
        self.assertIsInstance(breaches, list)

        sla_input = {
            "incident_id": unique_incident_id,
            "aggregated_data": aggregated,
            "threshold_seconds": 60
        }
        
        result = track_incident_sla(sla_input)
        self.assertEqual(result["incident_id"], unique_incident_id)
        self.assertTrue(result["breach_predicted"])


if __name__ == "__main__":
    unittest.main()