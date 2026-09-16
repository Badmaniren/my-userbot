import unittest
import uuid
import random
from skills.incident_sla_mitigation_planner import IncidentSLAMitigationPlanner, incident_sla_mitigation_planner

class TestIncidentSLAMitigationPlannerIntegration(unittest.TestCase):
    def setUp(self):
        self.planner = IncidentSLAMitigationPlanner()
        self.random_incident_id = f"inc-{uuid.uuid4()}-{random.randint(1000, 9999)}"
        self.random_custom_step = f"Action-{uuid.uuid4()}"

    def test_generate_mitigation_plan_integration(self):
        plan = self.planner.generate_mitigation_plan(self.random_incident_id)
        self.assertIsInstance(plan, dict)
        if plan:
            self.assertEqual(plan.get("incident_id"), self.random_incident_id)
            self.assertIn("tracker_id", plan)
            self.assertIn("steps", plan)
            self.assertIsInstance(plan["steps"], list)

    def test_build_plan_for_incident_integration(self):
        plan = self.planner.build_plan_for_incident(self.random_incident_id)
        self.assertIsInstance(plan, dict)
        self.assertEqual(plan.get("incident_id"), self.random_incident_id)
        self.assertIn("remediation_steps", plan)
        self.assertIn("risk_info", plan)
        self.assertIn("tracker_details", plan)
        self.assertIsInstance(plan["remediation_steps"], list)
        self.assertGreater(len(plan["remediation_steps"]), 0)

    def test_export_mitigation_report_integration(self):
        stream = self.planner.export_mitigation_report()
        self.assertIsNotNone(stream)
        content = stream.read()
        self.assertIsInstance(content, bytes)
        self.assertGreater(len(content), 0)

    def test_evaluate_and_mitigate_integration(self):
        try:
            self.planner.evaluate_and_mitigate(self.random_incident_id)
        except Exception as e:
            self.fail(f"evaluate_and_mitigate raised an exception unexpectedly: {e}")

    def test_entrypoint_payload_integration(self):
        payload = {
            "incident_id": self.random_incident_id,
            "prediction_payload": {
                "remediation_steps": [self.random_custom_step, "Validate system stability"]
            }
        }
        result = incident_sla_mitigation_planner(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("target_incident_id"), self.random_incident_id)
        self.assertIn("mitigation_plan_id", result)
        self.assertIn("status", result)
        self.assertEqual(result.get("status"), "generated")
        self.assertIn(self.random_custom_step, result.get("remediation_steps", []))

    def test_entrypoint_string_integration(self):
        result = incident_sla_mitigation_planner(self.random_incident_id)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("target_incident_id"), self.random_incident_id)
        self.assertIn("mitigation_plan_id", result)
        self.assertEqual(result.get("status"), "generated")

if __name__ == "__main__":
    unittest.main()