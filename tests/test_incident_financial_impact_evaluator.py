import unittest
from unittest.mock import patch
import os
import uuid
import random
import io
from skills.incident_financial_impact_evaluator import (
    IncidentFinancialImpactEvaluator,
    incident_financial_impact_evaluator
)

class TestIncidentFinancialImpactEvaluator(unittest.TestCase):

    def setUp(self):
        self.evaluator = IncidentFinancialImpactEvaluator()
        self.incident_id = str(uuid.uuid4())

    def test_evaluate_with_dict_impact_data_hours(self):
        downtime = round(random.uniform(1.0, 24.0), 2)
        rate = round(random.uniform(100.0, 5000.0), 2)
        impact_data = {
            "incident_id": self.incident_id,
            "downtime_hours": downtime
        }
        
        with patch.dict(os.environ, {"BASE_HOURLY_RATE_LOSS": str(rate)}):
            result = self.evaluator.evaluate(impact_data)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertEqual(result["total_financial_loss"], downtime * rate)
        self.assertEqual(result["estimated_loss_usd"], downtime * rate)

    def test_evaluate_with_dict_impact_data_minutes(self):
        minutes = round(random.uniform(30.0, 300.0), 2)
        rate = round(random.uniform(500.0, 2000.0), 2)
        impact_data = {
            "incident_id": self.incident_id,
            "downtime_minutes": minutes
        }
        
        with patch.dict(os.environ, {"BASE_HOURLY_RATE_LOSS": str(rate)}):
            result = self.evaluator.evaluate(impact_data)

        expected_hours = minutes / 60.0
        self.assertIsInstance(result, dict)
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertAlmostEqual(result["total_financial_loss"], expected_hours * rate)
        self.assertAlmostEqual(result["estimated_loss_usd"], expected_hours * rate)

    def test_evaluate_with_analyzer_fallback(self):
        downtime = round(random.uniform(2.0, 10.0), 2)
        rate = round(random.uniform(1000.0, 3000.0), 2)
        mock_impact_data = {
            "incident_id": self.incident_id,
            "downtime_hours": downtime
        }

        with patch("skills.incident_financial_impact_evaluator.IncidentImpactAnalyzer") as MockAnalyzer:
            instance = MockAnalyzer.return_value
            instance.get_impact_data.return_value = mock_impact_data

            with patch.dict(os.environ, {"BASE_HOURLY_RATE_LOSS": str(rate)}):
                result = self.evaluator.evaluate(self.incident_id)

            instance.get_impact_data.assert_called_once_with(self.incident_id)
            self.assertEqual(result["incident_id"], self.incident_id)
            self.assertEqual(result["total_financial_loss"], downtime * rate)

    def test_evaluate_missing_impact_data_raises_value_error(self):
        with patch("skills.incident_financial_impact_evaluator.IncidentImpactAnalyzer") as MockAnalyzer:
            instance = MockAnalyzer.return_value
            instance.get_impact_data.return_value = None

            with self.assertRaises(ValueError) as ctx:
                self.evaluator.evaluate(self.incident_id)
            self.assertIn("Impact data is missing", str(ctx.exception))

    def test_evaluate_invalid_impact_data_type_raises_value_error(self):
        invalid_data = str(uuid.uuid4())
        with patch("skills.incident_financial_impact_evaluator.IncidentImpactAnalyzer") as MockAnalyzer:
            instance = MockAnalyzer.return_value
            instance.get_impact_data.return_value = invalid_data

            with self.assertRaises(ValueError) as ctx:
                self.evaluator.evaluate(self.incident_id)
            self.assertIn("Impact data must be a dictionary", str(ctx.exception))

    def test_evaluate_invalid_downtime_falls_back_to_zero(self):
        bad_strings = [str(uuid.uuid4()), "abc", "NaN"]
        bad_val = random.choice(bad_strings)
        impact_data = {
            "incident_id": self.incident_id,
            "downtime_hours": bad_val,
            "downtime_minutes": bad_val
        }
        
        result = self.evaluator.evaluate(impact_data)
        self.assertEqual(result["total_financial_loss"], 0.0)

    def test_evaluate_invalid_hourly_rate_falls_back_to_default(self):
        downtime = 2.0
        bad_rate = str(uuid.uuid4())
        impact_data = {
            "incident_id": self.incident_id,
            "downtime_hours": downtime
        }

        with patch.dict(os.environ, {"BASE_HOURLY_RATE_LOSS": bad_rate}):
            result = self.evaluator.evaluate(impact_data)

        self.assertEqual(result["total_financial_loss"], downtime * 1000.0)

    def test_functional_helper_wrapper(self):
        downtime = round(random.uniform(1.0, 5.0), 2)
        impact_data = {
            "incident_id": self.incident_id,
            "downtime_hours": downtime
        }
        result = incident_financial_impact_evaluator(impact_data)
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertGreaterEqual(result["total_financial_loss"], 0.0)

if __name__ == "__main__":
    unittest.main()