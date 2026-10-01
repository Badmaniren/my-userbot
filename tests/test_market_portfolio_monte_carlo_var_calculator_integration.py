import unittest
import uuid
import random
import numpy as np

from skills.market_portfolio_monte_carlo_var_calculator import (
    MarketPortfolioMonteCarloVarCalculator,
    market_portfolio_monte_carlo_var_calculator,
    VaRCalculationError
)
from skills import db_storage

class TestMarketPortfolioMonteCarloVarCalculatorIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.simulation_runs = random.randint(100, 500)
        self.initial_value = round(random.uniform(50000.0, 200000.0), 2)

        self.calculator = MarketPortfolioMonteCarloVarCalculator(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            simulation_runs=self.simulation_runs
        )

    def test_calculate_var_integration(self):
        result = self.calculator.calculate_var(initial_value=self.initial_value)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['portfolio_id'], self.portfolio_id)
        self.assertEqual(result['confidence_level'], self.confidence_level)
        self.assertIn('var_absolute', result)
        self.assertIn('var_percentage', result)
        self.assertIn('expected_shortfall', result)

        self.assertGreaterEqual(result['var_absolute'], 0.0)
        self.assertGreaterEqual(result['var_percentage'], 0.0)
        self.assertGreaterEqual(result['expected_shortfall'], 0.0)

    def test_calculate_expected_shortfall_integration(self):
        es_result = self.calculator.calculate_expected_shortfall(initial_value=self.initial_value)

        self.assertIsInstance(es_result, dict)
        self.assertIn('expected_shortfall_absolute', es_result)
        self.assertIn('expected_shortfall_percentage', es_result)

        self.assertGreaterEqual(es_result['expected_shortfall_absolute'], 0.0)
        self.assertGreaterEqual(es_result['expected_shortfall_percentage'], 0.0)

    def test_functional_wrapper_integration(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "confidence_level": self.confidence_level,
            "simulation_data": {
                "initial_value": self.initial_value,
                "simulation_paths": [
                    [self.initial_value, self.initial_value * random.uniform(0.9, 1.1)]
                    for _ in range(self.simulation_runs)
                ]
            }
        }

        output = market_portfolio_monte_carlo_var_calculator(payload)

        self.assertIsInstance(output, dict)
        self.assertEqual(output['portfolio_id'], self.portfolio_id)
        self.assertEqual(output['confidence_level'], self.confidence_level)
        self.assertIn('var_value', output)
        self.assertIn('expected_shortfall', output)

        self.assertGreaterEqual(output['var_value'], 0.0)
        self.assertGreaterEqual(output['expected_shortfall'], 0.0)

    def test_invalid_confidence_level_raises_error(self):
        invalid_confidence = random.choice([-0.1, 0.0, 1.0, 1.5])
        with self.assertRaises(ValueError):
            calc = MarketPortfolioMonteCarloVarCalculator(
                portfolio_id=self.portfolio_id,
                confidence_level=invalid_confidence,
                simulation_runs=self.simulation_runs
            )
            calc.calculate_var(initial_value=self.initial_value)

if __name__ == '__main__':
    unittest.main()