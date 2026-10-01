import unittest
import uuid
import random
from skills.market_portfolio_var_monte_carlo_analyzer import (
    MarketPortfolioVaRMonteCarloAnalyzer,
    market_portfolio_var_monte_carlo_analyzer
)

class TestMarketPortfolioVaRMonteCarloAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"portfolio-{uuid.uuid4()}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.simulations = random.choice([500, 1000, 2000])
        self.horizon_days = random.randint(1, 10)
        self.analyzer = MarketPortfolioVaRMonteCarloAnalyzer()

    def test_compute_var_integration_flow(self):
        result = self.analyzer.compute_var(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            simulations=self.simulations,
            horizon_days=self.horizon_days
        )

        self.assertIn('portfolio_id', result)
        self.assertEqual(result['portfolio_id'], self.portfolio_id)
        self.assertIn('var_value', result)
        self.assertIn('expected_shortfall', result)
        self.assertGreaterEqual(result['var_value'], 0.0)
        self.assertGreaterEqual(result['expected_shortfall'], result['var_value'])

        stats = result.get('simulation_stats', {})
        self.assertEqual(stats.get('simulations_run'), self.simulations)
        self.assertEqual(stats.get('horizon_days'), self.horizon_days)

    def test_functional_wrapper_integration(self):
        stress_context_val = f"stress-scenario-{uuid.uuid4()}"
        wrapped_result = market_portfolio_var_monte_carlo_analyzer(
            portfolio_id=self.portfolio_id,
            confidence=self.confidence_level,
            simulations=self.simulations,
            stress_context=stress_context_val
        )

        self.assertEqual(wrapped_result['portfolio_id'], self.portfolio_id)
        self.assertEqual(wrapped_result['stress_context'], stress_context_val)
        self.assertIn('var_value', wrapped_result)

    def test_compute_stressed_var_integration(self):
        scenario_name = f"crash-{uuid.uuid4()}"
        stressed_result = self.analyzer.compute_stressed_var(
            portfolio_id=self.portfolio_id,
            scenario_name=scenario_name,
            confidence_level=self.confidence_level,
            simulations=self.simulations
        )

        self.assertEqual(stressed_result['portfolio_id'], self.portfolio_id)
        self.assertEqual(stressed_result['scenario'], scenario_name)
        self.assertIn('stressed_var', stressed_result)
        self.assertGreaterEqual(stressed_result['stressed_var'], 0.0)

if __name__ == '__main__':
    unittest.main()