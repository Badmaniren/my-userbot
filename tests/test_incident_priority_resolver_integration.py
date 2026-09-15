import unittest
import uuid
import random
import os
from skills.incident_priority_resolver import resolve_incident_priority
from skills.incident_aggregator import aggregate_incidents
from skills.incident_trend_analyzer import analyze_incident_trends

class TestIncidentPriorityResolverIntegration(unittest.TestCase):

    def test_resolve_incident_priority_integration(self):
        unique_incident_id = str(uuid.uuid4())
        random_error_count = random.randint(10, 5000)
        random_system_load = round(random.uniform(50.0, 99.9), 2)
        
        raw_incident_payload = {
            "incident_id": unique_incident_id,
            "error_count": random_error_count,
            "system_load": random_system_load,
            "metric_source": "integration_test_gateway"
        }

        aggregated_data = aggregate_incidents([raw_incident_payload])
        
        self.assertIn("aggregated_metrics", aggregated_data)
        
        trend_report = analyze_incident_trends(aggregated_data)
        
        self.assertIn("trend_coefficient", trend_report)

        resolved_priority_output = resolve_incident_priority(
            incident_id=unique_incident_id,
            trend_data=trend_report
        )

        self.assertIsInstance(resolved_priority_output, dict)
        self.assertEqual(resolved_priority_output.get("target_incident_id"), unique_incident_id)
        self.assertIn("priority_level", resolved_priority_output)
        
        artifact_path = resolved_priority_output.get("report_file_path")
        if artifact_path:
            self.assertTrue(os.path.exists(artifact_path))
            if os.path.exists(artifact_path):
                os.remove(artifact_path)

if __name__ == "__main__":
    unittest.main()