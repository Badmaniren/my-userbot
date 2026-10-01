import unittest
import uuid
import random
import os
from skills.market_portfolio_tail_risk_hedge_optimizer import market_portfolio_tail_risk_hedge_optimizer
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.db_storage import db_storage

class TestMarketPortfolioTailRiskHedgeoptimizerIntegration(unittest.TestCase):
    def test_tail_risk_hedge_optimizer_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        sim_runs = random.randint(100, 1000)
        confidence_level = round(random.uniform(0.95, 0.99), 4)

        mc_engine_result = market_portfolio_stress_monte_carlo_engine(
            portfolio_id=portfolio_id,
            simulations=sim_runs,
            confidence=confidence_level
        )

        self.assertIsNotNone(mc_engine_result, "Monte Carlo engine must return simulation data")

        optimizer_result = market_portfolio_tail_risk_hedge_optimizer(
            portfolio_id=portfolio_id,
            monte_carlo_data=mc_engine_result
        )

        self.assertIn("hedge_strategy_id", optimizer_result, "Optimizer must generate a hedge strategy ID")
        strategy_id = optimizer_result["hedge_strategy_id"]
        self.assertTrue(len(strategy_id) > 0, "Strategy ID must not be empty")

        stored_data = db_storage(
            action="get",
            key=f"hedge_strategy_{strategy_id}"
        )
        self.assertEqual(stored_data.get("portfolio_id"), portfolio_id, "Persisted portfolio ID must match")
        self.assertIn("optimal_assets", stored_data, "Storage must contain optimal hedging assets")

        output_filepath = f"reports/tail_risk_{strategy_id}.json"
        self.assertTrue(os.path.exists(output_filepath), "Tail risk hedge optimization report file must be created")

        if os.path.exists(output_filepath):
            os.remove(output_filepath)

if __name__ == "__main__":
    unittest.main()