import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_sla_tracker_full_integration(self):
        random_id = f"INC-{uuid.uuid4()}"
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severities)
        
        raw_event = {
            "id": random_id,
            "source": "integration_test",
            "metrics": {"latency": random.randint(100, 1000)}
        }

        aggregated = aggregate_incidents(raw_event)
        evaluated_severity = evaluate_incident_severity(aggregated)

        self.assertIn(evaluated_severity, severities)

        thresholds = {
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 600
        }
        
        tracker = IncidentSLATracker(sla_thresholds=thresholds, warning_threshold_pct=0.8)
        
        created_time = datetime.now() - timedelta(seconds=random.randint(10, 100))
        tracker.register_incident(incident_id=random_id, severity=evaluated_severity, created_at=created_time)
        
        time_to_breach = tracker.get_time_to_breach(incident_id=random_id)
        self.assertIsInstance(time_to_breach, float)

        sla_payload = {
            "incident_id": random_id,
            "aggregated_data": aggregated,
            "threshold_seconds": thresholds.get(evaluated_severity, 3600)
        }
        
        track_result = track_incident_sla(sla_payload)
        self.assertEqual(track_result["incident_id"], random_id)
        self.assertIsInstance(track_result["breach_predicted"], bool)
        self.assertIsInstance(track_result["time_remaining_seconds"], float)

        breach_check = tracker.check_sla_breaches()
        self.assertIsInstance(breach_check, list)

if __name__ == "__main__":
    unittest.main()