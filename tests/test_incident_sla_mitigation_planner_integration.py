import unittest
import uuid
import random
from skills.incident_sla_mitigation_planner import IncidentSLAMitigationPlanner, incident_sla_mitigation_planner
from skills import incident_sla_breach_predictor
from skills import incident_sla_tracker
from skills import incident_knowledge_base_searcher


class TestIncidentSLAMitigationPlannerIntegration(unittest.TestCase):

    def setUp(self):
        self.planner = IncidentSLAMitigationPlanner()
        self.random_incident_id = f"inc-{uuid.uuid4()}"
        self.random_tracker_id = f"trk-{uuid.uuid4()}"

    def test_generate_mitigation_plan_integration(self):
        unique_id = f"inc-gen-{uuid.uuid4().hex}"
        
        if hasattr(incident_sla_breach_predictor, "get_predicted_breaches"):
            try:
                incident_sla_breach_predictor.get_predicted_breaches()
            except Exception:
                pass

        if hasattr(incident_sla_tracker, "get_active_tracker"):
            try:
                incident_sla_tracker.get_active_tracker(unique_id)
            except Exception:
                pass

        result = self.planner.generate_mitigation_plan(unique_id)
        
        if result:
            self.assertIn("incident_id", result)
            self.assertEqual(result["incident_id"], unique_id)
            self.assertIn("tracker_id", result)
            self.assertIn("steps", result)
            self.assertIsInstance(result["steps"], list)

    def test_build_plan_for_incident_integration(self):
        unique_id = f"inc-build-{uuid.uuid4().hex}"
        
        if hasattr(incident_knowledge_base_searcher, "find_remediation_steps"):
            try:
                incident_knowledge_base_searcher.find_remediation_steps(unique_id)
            except Exception:
                pass

        result = self.planner.build_plan_for_incident(unique_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), unique_id)
        self.assertIn("remediation_steps", result)
        self.assertIn("risk_info", result)
        self.assertIn("tracker_details", result)
        self.assertIsInstance(result["remediation_steps"], list)
        self.assertTrue(len(result["remediation_steps"]) > 0)

    def test_export_mitigation_report_integration(self):
        report_stream = self.planner.export_mitigation_report()
        self.assertIsNotNone(report_stream)
        content = report_stream.read()
        self.assertIsInstance(content, bytes)
        self.assertTrue(len(content) > 0)

    def test_evaluate_and_mitigate_integration(self):
        unique_id = f"inc-eval-{uuid.uuid4().hex}"
        try:
            self.planner.evaluate_and_mitigate(unique_id)
        except Exception as e:
            self.fail(f"evaluate_and_mitigate raised an exception with real modules: {e}")

    def test_incident_sla_mitigation_planner_entrypoint_integration(self):
        custom_steps = [f"Step-{random.randint(100, 999)}", f"Step-{random.randint(1000, 9999)}"]
        payload = {
            "incident_id": self.random_incident_id,
            "prediction_payload": {
                "remediation_steps": custom_steps
            }
        }

        result = incident_sla_mitigation_planner(payload)

        self.assertIsInstance(result, dict)
        self.assertIn("mitigation_plan_id", result)
        self.assertEqual(result.get("target_incident_id"), self.random_incident_id)
        self.assertEqual(result.get("remediation_steps"), custom_steps)
        self.assertEqual(result.get("status"), "generated")

        string_payload = f"inc-str-{uuid.uuid4().hex}"
        result_str = incident_sla_mitigation_planner(string_payload)
        self.assertIsInstance(result_str, dict)
        self.assertEqual(result_str.get("target_incident_id"), string_payload)
        self.assertIn("remediation_steps", result_str)


if __name__ == "__main__":
    unittest.main()