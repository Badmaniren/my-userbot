import unittest
import uuid
import random
from skills.incident_business_loss_calculator import incident_business_loss_calculator
from skills.incident_impact_analyzer import incident_impact_analyzer
from skills.incident_severity_evaluator import incident_severity_evaluator

class TestIncidentBusinessLossCalculatorIntegration(unittest.TestCase):
    def test_calculate_business_loss_integration(self):
        rand_incident_id = str(uuid.uuid4())
        rand_downtime = random.randint(10, 120)
        rand_revenue_per_minute = round(random.uniform(50.0, 500.0), 2)
        rand_affected_users = random.randint(100, 5000)
        rand_currency = random.choice(["USD", "EUR", "GBP"])

        payload = {
            "incident_id": rand_incident_id,
            "revenue_per_minute": rand_revenue_per_minute,
            "currency": rand_currency,
            "impact_data": {
                "downtime_minutes": rand_downtime,
                "affected_users": rand_affected_users
            }
        }

        impact_analysis = incident_impact_analyzer(payload)
        self.assertIsInstance(impact_analysis, (dict, type(None)))

        severity_eval = incident_severity_evaluator(payload)
        self.assertIsInstance(severity_eval, (dict, type(None)))

        result = incident_business_loss_calculator(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), rand_incident_id)
        self.assertEqual(result.get("currency"), rand_currency)

        expected_loss = round(rand_downtime * rand_revenue_per_minute, 2)
        self.assertEqual(result.get("total_financial_loss"), expected_loss)

        expected_operational_score = float(rand_affected_users) * (float(rand_downtime) / 60.0)
        self.assertEqual(result.get("operational_impact_score"), expected_operational_score)
        self.assertEqual(result.get("operational_loss_index"), expected_operational_score)

if __name__ == "__main__":
    unittest.main()