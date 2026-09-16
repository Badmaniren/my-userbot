import unittest
from unittest.mock import patch
import uuid
import random

from skills.incident_sla_recovery_optimizer import (
    incident_sla_recovery_optimizer,
    optimize_recovery_workflow
)

class TestIncidentSlaRecoveryOptimizer(unittest.TestCase):

    def test_incident_sla_recovery_optimizer_basic_generation(self):
        rand_id = uuid.uuid4().hex
        rand_step = uuid.uuid4().hex
        severity_data = {"incident_id": rand_id}
        mitigation_plans = {"incident_id": rand_id, "steps": [rand_step]}

        result = incident_sla_recovery_optimizer(
            incident_id=None,
            severity_data=severity_data,
            breach_predictors={uuid.uuid4().hex: random.random()},
            mitigation_plans=mitigation_plans
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(result["optimized"])
        self.assertEqual(result["target_incident_id"], rand_id)
        self.assertIn(rand_step, result["steps"])
        self.assertIn("optimized_workflow_id", result)
        self.assertIsInstance(result["risk_score"], float)

    def test_incident_sla_recovery_optimizer_fallback_uuid(self):
        result = incident_sla_recovery_optimizer()

        self.assertIsInstance(result, dict)
        self.assertTrue(result["optimized"])
        self.assertIsNotNone(result["target_incident_id"])
        self.assertEqual(result["steps"], ["default_recovery_step"])
        self.assertGreaterEqual(result["risk_score"], 0.1)
        self.assertLessEqual(result["risk_score"], 0.9)

    def test_incident_sla_recovery_optimizer_from_mitigation_dict(self):
        rand_id = uuid.uuid4().hex
        mitigation_plans = {"id": rand_id, "steps": [uuid.uuid4().hex, uuid.uuid4().hex]}

        result = incident_sla_recovery_optimizer(mitigation_plans=mitigation_plans)

        self.assertEqual(result["target_incident_id"], rand_id)
        self.assertEqual(result["steps"], mitigation_plans["steps"])

    def test_optimize_recovery_workflow_valid(self):
        rand_id = uuid.uuid4().hex
        rand_step = uuid.uuid4().hex
        mitigation_plan = {"id": rand_id, "steps": [rand_step]}
        predictors = {uuid.uuid4().hex: random.uniform(0, 1)}

        result = optimize_recovery_workflow(mitigation_plan, predictors)

        self.assertIsInstance(result, dict)
        self.assertIn("workflow_id", result)
        self.assertTrue(result["optimized"])
        self.assertIsInstance(result["risk_score"], float)

    def test_optimize_recovery_workflow_string_step(self):
        mitigation_plan = {"id": uuid.uuid4().hex, "steps": uuid.uuid4().hex}
        predictors = {uuid.uuid4().hex: True}

        result = optimize_recovery_workflow(mitigation_plan, predictors)

        self.assertTrue(result["optimized"])
        self.assertIn("risk_score", result)

    def test_optimize_recovery_workflow_invalid_input(self):
        with self.assertRaises(ValueError):
            optimize_recovery_workflow(None, {})

        with self.assertRaises(ValueError):
            optimize_recovery_workflow({}, None)

        with self.assertRaises(ValueError):
            optimize_recovery_workflow(None, None)

    def test_incident_sla_recovery_optimizer_with_mocked_random(self):
        rand_id = uuid.uuid4().hex
        expected_risk = 0.42

        with patch('skills.incident_sla_recovery_optimizer.random.uniform', return_value=expected_risk) as mock_random:
            result = incident_sla_recovery_optimizer(incident_id=rand_id)
            mock_random.assert_called_once_with(0.1, 0.9)
            self.assertEqual(result["risk_score"], expected_risk)
            self.assertEqual(result["target_incident_id"], rand_id)

if __name__ == '__main__':
    unittest.main()