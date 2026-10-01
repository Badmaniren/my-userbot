import unittest
import os
import uuid
import random
from skills.market_portfolio_var_liquidity_adjusted_calculator import (
    MarketPortfolioVarLiquidityAdjustedCalculator,
    market_portfolio_var_liquidity_adjusted_calculator
)
from skills.db_storage import db_storage

class TestMarketPortfolioVarLiquidityAdjustedCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.stream_path = f"test_stream_{self.portfolio_id}.txt"
        self.report_path = f"report_{self.portfolio_id}.json"

        content = f"volume:{random.randint(500000, 2000000)},spread:{random.uniform(0.005, 0.02)}"
        with open(self.stream_path, "w", encoding="utf-8") as f:
            f.write(content)

    def tearDown(self):
        for path in [self.stream_path, self.report_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_integration_full_lvar_workflow(self):
        calc = MarketPortfolioVarLiquidityAdjustedCalculator(db_storage=db_storage)

        confidence = round(random.uniform(0.90, 0.99), 2)
        horizon = random.randint(1, 5)

        lvar_result = calc.compute_lvar(
            portfolio_id=self.portfolio_id,
            confidence_level=confidence,
            time_horizon_days=horizon
        )

        self.assertIn("lvar", lvar_result)
        self.assertEqual(lvar_result["portfolio_id"], self.portfolio_id)
        self.assertEqual(lvar_result["confidence_level"], confidence)
        self.assertEqual(lvar_result["time_horizon_days"], horizon)

        position_size = round(random.uniform(10000.0, 100000.0), 2)
        liquidity_cost = calc.estimate_liquidity_cost(
            position_size=position_size,
            stream_path=self.stream_path
        )
        self.assertGreaterEqual(liquidity_cost, 0.0)

        calc.persist_lvar_result(
            portfolio_id=self.portfolio_id,
            lvar_value=lvar_result["lvar"]
        )

        val_amount = round(random.uniform(5000.0, 50000.0), 2)
        slip_cost = round(random.uniform(5.0, 50.0), 2)

        functional_result = market_portfolio_var_liquidity_adjusted_calculator(
            portfolio_id=self.portfolio_id,
            valuation={"valuation": val_amount},
            slippage={"slippage": slip_cost},
            confidence_level=confidence,
            holding_period_days=horizon
        )

        self.assertEqual(functional_result["portfolio_id"], self.portfolio_id)
        self.assertTrue(functional_result["persisted"])
        self.assertTrue(os.path.exists(self.report_path))

        with open(self.report_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        self.assertIn(self.portfolio_id, file_content)

if __name__ == "__main__":
    unittest.main()