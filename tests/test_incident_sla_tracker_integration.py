import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_end_to_end_incident_lifecycle(self):
        rand_suffix = str(uuid.uuid4())[:8]
        incident_id = f"INC-{rand_suffix}"
        
        severity_input = {
            "incident_id": incident_id,
            "raw_text": f"Critical database timeout failure {rand_suffix}",
            "metrics": {"error_rate": random.uniform(0.8, 1.0)}
        }
        severity_result = evaluate_incident_severity(severity_input)
        severity = severity_result.get("severity", "HIGH")
        
        aggregator_input = {
            "incident_id": incident_id,
            "source": "integration_test_suite",
            "data": {
                "timestamp": datetime.now().timestamp(),
                "severity": severity
            }
        }
        aggregated = aggregate_incidents(aggregator_input)
        
        tracker = IncidentSLATracker(
            sla_thresholds={"HIGH": 10, "CRITICAL": 5},
            warning_threshold_pct=0.5
        )
        
        created_time = datetime.now() - timedelta(seconds=6)
        tracker.register_incident(incident_id=incident_id, severity=severity, created_at=created_time)
        
        time_to_breach = tracker.get_time_to_breach(incident_id)
        self.assertIsInstance(time_to_breach, float)
        
        breaches = tracker.check_sla_breaches(current_time=datetime.now())

        breach_found = False
        for b in breaches:
            if b["incident_id"] == incident_id:
                breach_found = True
                self.assertIn(b["status"], ["WARNING", "BREACHED"])

        self.assertTrue(breach_found, f"Incident {incident_id} should have triggered SLA status update")
        
        sla_input = {
            "incident_id": incident_id,
            "aggregated_data": aggregated,
            "threshold_seconds": 10
        }
        prediction = track_incident_sla(sla_input)
        
        self.assertEqual(prediction["incident_id"], incident_id)
        self.assertIn("breach_predicted", prediction)
        self.assertIn("time_remaining_seconds", prediction)

if __name__ == "__main__":
    unittest.main()