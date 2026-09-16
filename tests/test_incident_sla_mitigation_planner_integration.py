import unittest
import uuid
import random
from skills.incident_sla_mitigation_planner import incident_sla_mitigation_planner
from skills.incident_sla_breach_predictor import incident_sla_breach_predictor
from skills.incident_sla_tracker import incident_sla_tracker

class TestIncidentSlaMitigationPlannerIntegration(unittest.TestCase):
    def test_mitigation_planner_integration_real_flow(self):
        unique_incident_id = f"inc-{uuid.uuid4()}"
        random_severity_score = round(random.uniform(7.0, 10.0), 2)
        random_breach_probability = round(random.uniform(0.85, 0.99), 2)

        tracker_input = {
            "incident_id": unique_incident_id,
            "status": "active",
            "severity_score": random_severity_score
        }
        tracker_result = incident_sla_tracker(tracker_input)

        predictor_input = {
            "incident_id": unique_incident_id,
            "breach_probability": random_breach_probability,
            "tracker_data": tracker_result
        }
        predictor_result = incident_sla_breach_predictor(predictor_input)

        planner_input = {
            "incident_id": unique_incident_id,
            "prediction_payload": predictor_result,
            "tracker_payload": tracker_result
        }
        
        mitigation_plan = incident_sla_mitigation_planner(planner_input)

        self.assertIsInstance(mitigation_plan, dict, "Mitigation planner must return a dictionary payload.")
        self.assertIn("mitigation_plan_id", mitigation_plan, "The output must contain a mitigation plan ID.")
        self.assertEqual(mitigation_plan.get("target_incident_id"), unique_incident_id, "The plan must be bound to the generated incident UUID.")
        self.assertIsInstance(mitigation_plan.get("remediation_steps"), list, "Remediation steps must be provided as a list.")
        self.assertTrue(len(mitigation_plan.get("remediation_steps")) > 0, "Generated mitigation plan must contain at least one remediation step.")

if __name__ == "__main__":
    unittest.main()