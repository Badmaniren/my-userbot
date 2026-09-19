import unittest
import os
import uuid
import random

from skills.incident_predictive_risk_model import incident_predictive_risk_model, start_new


class TestIncidentPredictiveRiskModelIntegration(unittest.TestCase):

    def test_incident_predictive_risk_model_flow(self):
        random_system_id = f"sys-{uuid.uuid4()}"
        predictive_input = {
            "system_id": random_system_id,
            "metric_threshold": random.randint(50, 100),
            "scope": f"scope-{uuid.uuid4()}"
        }

        artifact_path = f"/tmp/risk_report_{random_system_id}.json"
        if os.path.exists(artifact_path):
            os.remove(artifact_path)

        result = incident_predictive_risk_model(predictive_input)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("target_system_id"), random_system_id)
        self.assertIn("risk_assessment_id", result)
        self.assertIn("predicted_risk_score", result)
        self.assertEqual(result.get("status"), "success")

        self.assertTrue(os.path.exists(artifact_path), "Artifact file should be created by the module")
        
        with open(artifact_path, "r") as f:
            content = f.read()
            self.assertIn(random_system_id, content)
            self.assertIn(result["risk_assessment_id"], content)

        if os.path.exists(artifact_path):
            os.remove(artifact_path)

    def test_start_new_execution(self):
        start_args = {
            "param_id": str(uuid.uuid4()),
            "weight": random.uniform(1.0, 10.0)
        }
        
        response = start_new(start_args)

        self.assertIsInstance(response, dict)
        self.assertEqual(response.get("status"), "success")
        self.assertIn("metric_id", response)
        self.assertIsInstance(response.get("value"), float)
        self.assertTrue(0.0 <= response.get("value") <= 100.0)


if __name__ == "__main__":
    unittest.main()