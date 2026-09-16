import unittest
import uuid
import random
import os
from skills.incident_auto_escalation_engine import incident_auto_escalation_engine
from skills.incident_severity_evaluator import incident_severity_evaluator
from skills.incident_aggregator import incident_aggregator
from skills.incident_notification_bridge import incident_notification_bridge

class TestIncidentAutoEscalationIntegration(unittest.TestCase):
    def test_auto_escalation_real_integration(self):
        unique_incident_id = str(uuid.uuid4())
        random_error_code = random.randint(500, 599)
        random_score = round(random.uniform(7.5, 10.0), 2)

        raw_incident_data = {
            "incident_id": unique_incident_id,
            "error_code": random_error_code,
            "metric_value": random_score,
            "source": "integration_test_suite"
        }

        aggregated_incident = incident_aggregator(raw_incident_data)
        self.assertIn("incident_id", aggregated_incident)
        self.assertEqual(aggregated_incident["incident_id"], unique_incident_id)

        evaluated_incident = incident_severity_evaluator(aggregated_incident)
        self.assertIn("severity_score", evaluated_incident)
        self.assertGreaterEqual(evaluated_incident["severity_score"], 0.0)

        escalation_result = incident_auto_escalation_engine(evaluated_incident)
        self.assertIsInstance(escalation_result, dict)
        self.assertEqual(escalation_result.get("target_incident_id"), unique_incident_id)
        self.assertTrue(escalation_result.get("escalated", False))

        bridge_response = incident_notification_bridge(escalation_result)
        self.assertIsInstance(bridge_response, dict)
        self.assertEqual(bridge_response.get("status"), "dispatched")

        if "artifact_path" in escalation_result:
            self.assertTrue(os.path.exists(escalation_result["artifact_path"]))

if __name__ == "__main__":
    unittest.main()