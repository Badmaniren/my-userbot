import unittest
import uuid
import random
import os
from skills.security_incident_dashboard_aggregator import incident_aggregator
from skills.vulnerability_scanner import vulnerability_scanner
from skills.incident_severity_evaluator import incident_severity_evaluator

class TestSecurityIncidentDashboardAggregatorIntegration(unittest.TestCase):
    def test_dashboard_aggregation_real_flow(self):
        random_suffix = uuid.uuid4().hex[:8]
        test_incident_id = f"INC-{random_suffix}"
        test_vuln_id = f"VULN-{random.randint(1000, 9999)}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        vuln_data = vulnerability_scanner(target_id=test_vuln_id, severity=severity_level)
        self.assertIsNotNone(vuln_data)

        evaluated_incident = incident_severity_evaluator(incident_id=test_incident_id, level=severity_level)
        self.assertIsNotNone(evaluated_incident)

        dashboard_result = incident_aggregator(
            incident_id=test_incident_id,
            vulnerability_id=test_vuln_id,
            include_metrics=True
        )

        self.assertIsInstance(dashboard_result, dict)
        self.assertIn("dashboard_id", dashboard_result)
        self.assertEqual(dashboard_result.get("incident_id"), test_incident_id)
        self.assertEqual(dashboard_result.get("vulnerability_id"), test_vuln_id)

        output_file_path = f"dashboard_{test_incident_id}.json"
        if os.path.exists(output_file_path):
            self.assertTrue(os.path.getsize(output_file_path) > 0)
            os.remove(output_file_path)

if __name__ == "__main__":
    unittest.main()