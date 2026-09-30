import unittest
import uuid
import random
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine_run
from skills.market_portfolio_monte_carlo_var_analyzer import (
    MarketPortfolioMonteCarloVarAnalyzer,
    market_portfolio_monte_carlo_var_analyzer_run
)

class TestMarketPortfolioMonteCarloVarAnalyzerIntegration(unittest.TestCase):
    def test_var_analyzer_integration_with_engine(self):
        portfolio_id = str(uuid.uuid4())
        confidence_level = round(random.uniform(0.90, 0.99), 2)

        initial_capital = random.uniform(10000.0, 100000.0)
        scenario_count = random.randint(50, 200)

        engine_result = market_portfolio_stress_monte_carlo_engine_run(
            portfolio_id=portfolio_id,
            initial_capital=initial_capital,
            num_simulations=scenario_count
        )

        self.assertIsInstance(engine_result, dict)

        analyzer = MarketPortfolioMonteCarloVarAnalyzer(monte_carlo_engine=None)

        analysis_result = market_portfolio_monte_carlo_var_analyzer_run(
            portfolio_id=portfolio_id,
            monte_carlo_data=engine_result,
            confidence=confidence_level
        )

        self.assertIsInstance(analysis_result, dict)
        self.assertEqual(analysis_result["portfolio_id"], portfolio_id)
        self.assertEqual(analysis_result["confidence_level"], confidence_level)
        self.assertGreaterEqual(analysis_result["var"], 0.0)
        self.assertGreaterEqual(analysis_result["cvar"], 0.0)

if __name__ == "__main__":
    unittest.main()