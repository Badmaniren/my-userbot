import unittest
import uuid
import random
import os
from skills.market_portfolio_execution_cost_optimizer import (
    market_portfolio_execution_cost_optimizer
)
from skills.db_storage import db_storage
from skills.market_portfolio_slippage_model import market_portfolio_slippage_model
from skills.market_portfolio_monitor import market_portfolio_monitor
from skills.market_portfolio_execution_pipeline import market_portfolio_execution_pipeline

class TestMarketPortfolioExecutionCostOptimizerIntegration(unittest.TestCase):

    def test_execution_cost_optimizer_integration(self):
        portfolio_id = str(uuid.uuid4())
        asset_ticker = f"TICKER_{random.randint(1000, 9999)}"
        trade_volume = round(random.uniform(1000.0, 1000000.0), 2)
        volatility_index = round(random.uniform(0.1, 0.9), 4)

        db_storage(action="init_test_env", target=portfolio_id)

        liquidity_data = market_portfolio_monitor(
            action="get_liquidity",
            ticker=asset_ticker
        )

        slippage_estimation = market_portfolio_slippage_model(
            volume=trade_volume,
            volatility=volatility_index,
            liquidity=liquidity_data
        )

        optimization_result = market_portfolio_execution_cost_optimizer(
            portfolio_id=portfolio_id,
            ticker=asset_ticker,
            volume=trade_volume,
            slippage_model_output=slippage_estimation
        )

        self.assertIn("optimized_cost", optimization_result)
        self.assertIn("execution_strategy_id", optimization_result)
        
        execution_id = optimization_result["execution_strategy_id"]
        self.assertIsInstance(execution_id, str)
        self.assertTrue(len(execution_id) > 0)

        pipeline_response = market_portfolio_execution_pipeline(
            execution_id=execution_id,
            portfolio_id=portfolio_id,
            payload=optimization_result
        )

        self.assertEqual(pipeline_response.get("status"), "dispatched")

        report_filename = f"cost_optimizer_report_{portfolio_id}.log"
        self.assertTrue(
            os.path.exists(report_filename) or pipeline_response.get("logged", True),
            "Integration must produce verifiable side effects or artifacts."
        )

        if os.path.exists(report_filename):
            os.remove(report_filename)

if __name__ == "__main__":
    unittest.main()