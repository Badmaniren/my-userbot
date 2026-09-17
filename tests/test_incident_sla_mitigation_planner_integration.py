import unittest
import uuid
import random
from skills.incident_sla_mitigation_planner import (
    IncidentSLAMitigationPlanner,
    incident_sla_mitigation_planner
)
from skills import incident_sla_breach_predictor
from skills import incident_sla_tracker
from skills import incident_knowledge_base_searcher
from skills import incident_auto_escalation_engine
from skills import recovery_report_exporter

class TestIncidentSLAMitigationPlannerIntegration(unittest.TestCase):
    def setUp(self):
        self.planner = IncidentSLAMitigationPlanner()
        self.random_incident_id = f"inc-test-{uuid.uuid4().hex[:8]}"
        self.random_steps = [f"Step-{random.randint(100, 999)}: Check metrics", f"Step-{random.randint(1000, 9999)}: Restart service"]

    def test_end_to_end_mitigation_workflow(self):
        payload = {
            "incident_id": self.random_incident_id,
            "prediction_payload": {
                "remediation_steps": self.random_steps
            }
        }

        result = incident_sla_mitigation_planner(payload)

        self.assertIsInstance(result, dict)
        self.assertIn("mitigation_plan_id", result)
        self.assertEqual(result["target_incident_id"], self.random_incident_id)
        self.assertEqual(result["remediation_steps"], self.random_steps)
        self.assertEqual(result["status"], "generated")

    def test_class_methods_integration_with_real_modules(self):
        plan_result = self.planner.generate_mitigation_plan(self.random_incident_id)
        self.assertIsInstance(plan_result, dict)

        built_plan = self.planner.build_plan_for_incident(self.random_incident_id)
        self.assertIsInstance(built_plan, dict)
        self.assertEqual(built_plan.get("incident_id"), self.random_incident_id)
        self.assertIn("remediation_steps", built_plan)
        self.assertIn("risk_info", built_plan)
        self.assertIn("tracker_details", built_plan)

        report_stream = self.planner.export_mitigation_report()
        self.assertTrue(hasattr(report_stream, "read"))

        try:
            self.planner.evaluate_and_mitigate(self.random_incident_id)
        except Exception as e:
            self.fail(f"evaluate_and_mitigate raised an exception with real modules: {e}")

if __name__ == "__main__":
    unittest.main()