import unittest
import uuid
import random
import os
from skills.market_portfolio_hedge_synthesizer import market_portfolio_hedge_synthesizer
from skills.market_portfolio_backtester import market_portfolio_backtester
from skills.market_portfolio_strategy_optimizer import market_portfolio_strategy_optimizer
from skills.db_storage import db_storage

class TestMarketPortfolioHedgeSynthesizerIntegration(unittest.TestCase):

    def test_hedge_synthesizer_integration_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_capital = round(random.uniform(50000.0, 500000.0), 2)
        var_threshold = round(random.uniform(0.01, 0.05), 4)

        optimizer_result = market_portfolio_strategy_optimizer(
            portfolio_id=portfolio_id,
            target_return=0.12,
            risk_tolerance=var_threshold
        )
        self.assertIsNotNone(optimizer_result)

        backtest_result = market_portfolio_backtester(
            portfolio_id=portfolio_id,
            capital=initial_capital,
            simulation_steps=random.randint(30, 100)
        )
        self.assertIn("status", backtest_result)

        hedge_params = market_portfolio_hedge_synthesizer(
            portfolio_id=portfolio_id,
            var_limit=var_threshold,
            market_data_ref=backtest_result.get("data_ref", "default_ref")
        )

        self.assertIsInstance(hedge_params, dict)
        self.assertIn("hedge_id", hedge_params)

        generated_hedge_id = hedge_params["hedge_id"]
        self.assertTrue(len(generated_hedge_id) > 0)

        saved_state = db_storage(
            action="get",
            entity_id=generated_hedge_id
        )

        self.assertIsNotNone(saved_state)
        self.assertEqual(saved_state.get("portfolio_id"), portfolio_id)

if __name__ == "__main__":
    unittest.main()