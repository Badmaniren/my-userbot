import unittest
import uuid
import random

from skills.incident_severity_evaluator import incident_severity_evaluator
from skills.incident_sla_breach_predictor import incident_sla_breach_predictor
from skills.incident_sla_mitigation_planner import incident_sla_mitigation_planner
from skills.incident_sla_recovery_optimizer import incident_sla_recovery_optimizer, optimize_recovery_workflow

class TestIncidentSlaRecoveryOptimizerIntegration(unittest.TestCase):
    def test_end_to_end_recovery_optimizer_integration(self):
        dynamic_incident_id = f"inc-{uuid.uuid4()}"
        dynamic_severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        dynamic_risk_factor = random.uniform(0.05, 0.95)
        dynamic_step_name = f"step_remediate_{uuid.uuid4().hex[:6]}"

        severity_input = {
            "incident_id": dynamic_incident_id,
            "severity": dynamic_severity_level
        }
        severity_result = incident_severity_evaluator(severity_data=severity_input)

        predictor_input = {
            "incident_id": dynamic_incident_id,
            "risk_factor": dynamic_risk_factor
        }
        predictor_result = incident_sla_breach_predictor(breach_data=predictor_input)

        planner_input = {
            "incident_id": dynamic_incident_id,
            "steps": [dynamic_step_name, "verify_system_stability"]
        }
        planner_result = incident_sla_mitigation_planner(mitigation_data=planner_input)

        optimizer_result = incident_sla_recovery_optimizer(
            incident_id=dynamic_incident_id,
            severity_data=severity_result,
            breach_predictors=predictor_result,
            mitigation_plans=planner_result
        )

        self.assertIsInstance(optimizer_result, dict)
        self.assertEqual(optimizer_result.get("target_incident_id"), dynamic_incident_id)
        self.assertTrue(optimizer_result.get("optimized"))
        self.assertIn("optimized_workflow_id", optimizer_result)
        self.assertIn(dynamic_step_name, optimizer_result.get("steps", []))
        self.assertIsInstance(optimizer_result.get("risk_score"), float)

        workflow_result = optimize_recovery_workflow(
            mitigation_plan=planner_result,
            predictors=predictor_result
        )

        self.assertIsInstance(workflow_result, dict)
        self.assertIn("workflow_id", workflow_result)
        self.assertTrue(workflow_result.get("optimized"))
        self.assertIsInstance(workflow_result.get("risk_score"), float)

    def test_optimize_recovery_workflow_invalid_input(self):
        with self.assertRaises(ValueError):
            optimize_recovery_workflow(None, None)

if __name__ == "__main__":
    unittest.main()