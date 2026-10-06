import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_scenario_matrix_evaluator import MarketPortfolioStressScenarioMatrixEvaluator
from skills.market_portfolio_execution_cost_optimizer import MarketPortfolioExecutionCostOptimizer
from skills.market_portfolio_stress_hedge_planner import (
    plan_portfolio_stress_hedge,
    MarketPortfolioStressHedgePlanner
)

class TestMarketPortfolioStressHedgePlannerIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.historical_window = random.randint(30, 365)
        self.asset = f"ASSET_{random.randint(100, 999)}"
        self.ticker = f"TICK_{random.randint(1000, 9999)}"
        self.volume = round(random.uniform(10.0, 5000.0), 2)
        self.slippage_output = {"slippage_rate": round(random.uniform(0.001, 0.05), 4)}
        self.db_storage = f"test_db_{uuid.uuid4().hex}.db"

    def tearDown(self):
        if os.path.exists(self.db_storage):
            try:
                os.remove(self.db_storage)
            except OSError:
                pass

    def test_stress_hedge_planner_composition(self):
        evaluator = MarketPortfolioStressScenarioMatrixEvaluator(
            db_storage=self.db_storage,
            extractor_tool_1790087207="dummy_ext_1",
            extractor_tool_1790102839="dummy_ext_2"
        )
        matrix_result = evaluator.evaluate_matrix(
            portfolio_id=self.portfolio_id,
            historical_window=self.historical_window
        )
        self.assertIsInstance(matrix_result, dict)

        optimizer = MarketPortfolioExecutionCostOptimizer()
        optimization_result = optimizer.optimize_execution_cost(
            portfolio_id=self.portfolio_id,
            asset=self.asset,
            volume=self.volume,
            ticker=self.ticker,
            slippage_model_output=self.slippage_output
        )

        planner_instance = MarketPortfolioStressHedgePlanner()
        self.assertTrue(hasattr(planner_instance, "plan_hedge"))

        hedge_plan = plan_portfolio_stress_hedge(
            portfolio_id=self.portfolio_id,
            ticker=self.ticker,
            volume=self.volume,
            historical_window=self.historical_window,
            slippage_model_output=self.slippage_output
        )

        self.assertIsInstance(hedge_plan, dict)
        self.assertIn("hedge_orders", hedge_plan)
        self.assertIn("total_estimated_cost", hedge_plan)

        order_id = str(uuid.uuid4())
        target_price = round(random.uniform(10.0, 1500.0), 2)
        execution_id = str(uuid.uuid4())
        payload = {"hedge_vector": hedge_plan, "random_salt": random.randint(1, 100000)}

        route_response = optimizer.route_to_execution_pipeline(
            order_id=order_id,
            target_price=target_price,
            execution_id=execution_id,
            portfolio_id=self.portfolio_id,
            payload=payload
        )
        self.assertIsNotNone(route_response)

if __name__ == "__main__":
    unittest.main()