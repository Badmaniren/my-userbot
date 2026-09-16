import unittest
import uuid
import random
import time
from skills.incident_sla_tracker import track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_sla_tracker_integration_real_flow(self):
        unique_suffix = str(uuid.uuid4())[:8]
        incident_id = f"inc-{unique_suffix}-{random.randint(1000, 9999)}"
        system_id = f"sys-{random.randint(100, 999)}"
        
        raw_payload = {
            "incident_id": incident_id,
            "system_id": system_id,
            "metric": "response_time_ms",
            "value": random.randint(500, 5000),
            "timestamp": time.time()
        }

        severity_result = evaluate_incident_severity(raw_payload)
        
        aggregator_payload = {
            "incident_id": incident_id,
            "severity": severity_result.get("severity", "HIGH"),
            "data": raw_payload
        }
        
        aggregated_incident = aggregate_incidents(aggregator_payload)
        
        sla_input = {
            "incident_id": incident_id,
            "aggregated_data": aggregated_incident,
            "threshold_seconds": random.randint(60, 3600)
        }
        
        sla_result = track_incident_sla(sla_input)

        self.assertIsInstance(sla_result, dict)
        self.assertEqual(sla_result.get("incident_id"), incident_id)
        self.assertIn("breach_predicted", sla_result)
        self.assertIn("time_remaining_seconds", sla_result)

if __name__ == "__main__":
    unittest.main()