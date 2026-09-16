import unittest
import uuid
import random
from skills.incident_business_loss_estimator import incident_business_loss_estimator
from skills.incident_impact_analyzer import incident_impact_analyzer

class TestIncidentBusinessLossEstimatorIntegration(unittest.TestCase):
    def test_loss_estimation_integration(self):
        random_id = str(uuid.uuid4())
        random_downtime_minutes = random.randint(10, 1440)
        random_users_affected = random.randint(100, 50000)

        impact_input_data = {
            "incident_id": random_id,
            "downtime_minutes": random_downtime_minutes,
            "affected_users": random_users_affected,
            "severity": "HIGH"
        }

        impact_analysis_result = incident_impact_analyzer(impact_input_data)

        self.assertIsInstance(impact_analysis_result, dict)

        estimator_input_data = {
            "incident_id": random_id,
            "impact_data": impact_analysis_result,
            "base_cost_per_minute": round(random.uniform(10.0, 500.0), 2)
        }

        loss_estimation_result = incident_business_loss_estimator(estimator_input_data)

        self.assertIsInstance(loss_estimation_result, dict)
        self.assertIn("total_financial_loss", loss_estimation_result)
        self.assertIn("incident_id", loss_estimation_result)
        self.assertEqual(loss_estimation_result["incident_id"], random_id)
        self.assertGreater(loss_estimation_result["total_financial_loss"], 0.0)

if __name__ == "__main__":
    unittest.main()