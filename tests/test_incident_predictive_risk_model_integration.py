import unittest
import uuid
import random
import os
from skills.incident_predictive_risk_model import incident_predictive_risk_model, start_new

class TestIncidentPredictiveRiskModelIntegration(unittest.TestCase):
    def test_predictive_risk_model_integration(self):
        random_score = round(random.uniform(10.0, 90.0), 2)
        unique_run_id = str(uuid.uuid4())

        severity_data = {"score": random_score}
        telemetry_snapshot = {"cpu_load": random.randint(1, 100), "memory_usage": random.randint(10, 95)}

        result = incident_predictive_risk_model(
            severity_data=severity_data,
            telemetry_snapshot=telemetry_snapshot,
            run_id=unique_run_id
        )

        self.assertIsInstance(result, dict)
        self.assertIn("risk_score", result)
        self.assertIn("preventive_action_required", result)
        self.assertIn("log_path", result)

        self.assertEqual(result["risk_score"], random_score)
        self.assertEqual(result["preventive_action_required"], random_score > 50.0)
        self.assertEqual(result["log_path"], f"risk_audit_{unique_run_id}.log")

        random_target = str(uuid.uuid4())
        random_token = str(uuid.uuid4())

        start_result = start_new(
            target=random_target,
            probability_limit=random.uniform(0.1, 0.9),
            audit_token=random_token
        )
        self.assertIsNone(start_result)

if __name__ == "__main__":
    unittest.main()