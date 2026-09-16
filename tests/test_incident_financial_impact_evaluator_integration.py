import unittest
import uuid
import random
from skills.incident_impact_analyzer import incident_impact_analyzer
from skills.incident_financial_impact_evaluator import incident_financial_impact_evaluator

class TestIncidentFinancialImpactEvaluatorIntegration(unittest.TestCase):
    def test_evaluate_financial_impact_real_flow(self):
        random_incident_id = f"inc-{uuid.uuid4()}"
        random_downtime_minutes = random.randint(10, 1440)
        random_affected_users = random.randint(100, 50000)
        
        raw_impact_data = {
            "incident_id": random_incident_id,
            "downtime_minutes": random_downtime_minutes,
            "affected_users": random_affected_users,
            "severity": random.choice(["HIGH", "CRITICAL", "MEDIUM"])
        }
        
        analyzed_impact = incident_impact_analyzer(raw_impact_data)
        
        self.assertIsInstance(analyzed_impact, dict)
        self.assertIn("incident_id", analyzed_impact)
        
        financial_evaluation = incident_financial_impact_evaluator(analyzed_impact)
        
        self.assertIsInstance(financial_evaluation, dict)
        self.assertEqual(financial_evaluation.get("incident_id"), random_incident_id)
        self.assertIn("estimated_loss_usd", financial_evaluation)
        self.assertGreaterEqual(financial_evaluation["estimated_loss_usd"], 0.0)

    def test_evaluate_financial_impact_error_handling(self):
        invalid_input = {
            "incident_id": f"err-{uuid.uuid4()}",
            "downtime_minutes": "invalid_number",
            "affected_users": -999
        }
        
        try:
            result = incident_financial_impact_evaluator(invalid_input)
            self.assertTrue(
                isinstance(result, dict) and (result.get("error") or result.get("estimated_loss_usd") == 0.0),
                "Module must gracefully handle invalid data and return an error or zero loss."
            )
        except Exception as e:
            self.assertIsInstance(e, (ValueError, TypeError, KeyError))

if __name__ == "__main__":
    unittest.main()