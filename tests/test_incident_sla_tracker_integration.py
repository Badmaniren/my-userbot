import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_end_to_end_sla_tracker_integration(self):
        unique_incident_id = f"inc-{uuid.uuid4()}"
        raw_severity_input = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        severity_result = evaluate_incident_severity(
            module_name="test_module",
            exception=Exception(f"Simulated error with severity {raw_severity_input}"),
            traceback_str="Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\nException",
            incident_id=unique_incident_id
        )
        evaluated_severity = severity_result.get("severity", "MEDIUM")
        
        past_timestamp = datetime.now().timestamp() - random.randint(10, 100)
        aggregated_output = aggregate_incidents(
            module_name="test_module",
            exception=Exception(f"Simulated error with severity {raw_severity_input}"),
            traceback_str="Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\nException"
        )
        if "data" not in aggregated_output:
            aggregated_output["data"] = {}
        aggregated_output["data"]["timestamp"] = past_timestamp

        sla_thresholds = {
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 600
        }
        
        tracker = IncidentSLATracker(sla_thresholds=sla_thresholds, warning_threshold_pct=0.5)
        
        created_datetime = datetime.fromtimestamp(past_timestamp)
        tracker.register_incident(
            incident_id=unique_incident_id,
            severity=evaluated_severity,
            created_at=created_datetime
        )
        
        time_to_breach = tracker.get_time_to_breach(unique_incident_id)
        self.assertIsInstance(time_to_breach, float)
        
        sla_input_payload = {
            "incident_id": unique_incident_id,
            "aggregated_data": aggregated_output,
            "threshold_seconds": sla_thresholds[evaluated_severity]
        }
        
        tracking_result = track_incident_sla(sla_input_payload)
        self.assertEqual(tracking_result["incident_id"], unique_incident_id)
        self.assertIn("breach_predicted", tracking_result)
        self.assertIn("time_remaining_seconds", tracking_result)
        
        breach_check_results = tracker.check_sla_breaches()
        self.assertIsInstance(breach_check_results, list)

if __name__ == "__main__":
    unittest.main()