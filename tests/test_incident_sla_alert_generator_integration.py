import unittest
import uuid
import random
import os
from skills.incident_sla_alert_generator import incident_sla_alert_generator
from skills.incident_sla_tracker import incident_sla_tracker
from skills.incident_aggregator import incident_aggregator
from skills.incident_severity_evaluator import incident_severity_evaluator

class IntegrationTestIncidentSlaAlertGenerator(unittest.TestCase):
    def test_sla_alert_generator_end_to_end(self):
        unique_incident_id = str(uuid.uuid4())
        metric_value = random.randint(10, 500)

        raw_incident_data = {
            "id": unique_incident_id,
            "metric": metric_value,
            "status": "active"
        }

        aggregated_data = incident_aggregator(raw_incident_data)
        severity_result = incident_severity_evaluator(aggregated_data)
        sla_tracking_data = incident_sla_tracker(severity_result)

        alert_output = incident_sla_alert_generator(sla_tracking_data)

        self.assertIsInstance(alert_output, dict)
        self.assertIn("alert_id", alert_output)
        self.assertEqual(alert_output.get("incident_id"), unique_incident_id)
        self.assertTrue(alert_output.get("breach_visible", False))

if __name__ == "__main__":
    unittest.main()