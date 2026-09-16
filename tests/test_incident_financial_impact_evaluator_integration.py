import unittest
import uuid
import os
from skills.incident_financial_impact_evaluator import IncidentFinancialImpactEvaluator, incident_financial_impact_evaluator
from skills.incident_impact_analyzer import IncidentImpactAnalyzer

class TestIncidentFinancialImpactEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.evaluator = IncidentFinancialImpactEvaluator()
        self.analyzer = IncidentImpactAnalyzer()
        self.random_incident_id = f"inc-{uuid.uuid4()}"
        os.environ["BASE_HOURLY_RATE_LOSS"] = "1500.0"

    def test_evaluate_with_real_impact_data_dict(self):
        random_downtime = float(uuid.uuid4().int % 10) + 1.5
        impact_data = {
            "incident_id": self.random_incident_id,
            "downtime_hours": random_downtime
        }
        
        result = self.evaluator.evaluate(impact_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), self.random_incident_id)
        expected_loss = random_downtime * 1500.0
        self.assertEqual(result.get("total_financial_loss"), expected_loss)
        self.assertEqual(result.get("estimated_loss_usd"), expected_loss)

    def test_evaluate_with_downtime_minutes(self):
        random_minutes = float(uuid.uuid4().int % 120) + 30.0
        impact_data = {
            "incident_id": self.random_incident_id,
            "downtime_minutes": random_minutes
        }
        
        result = incident_financial_impact_evaluator(impact_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), self.random_incident_id)
        expected_hours = random_minutes / 60.0
        expected_loss = expected_hours * 1500.0
        self.assertAlmostEqual(result.get("total_financial_loss"), expected_loss)

    def test_evaluate_missing_data_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.evaluator.evaluate(None)

    def test_evaluate_invalid_type_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.evaluator.evaluate(123456789)

if __name__ == "__main__":
    unittest.main()