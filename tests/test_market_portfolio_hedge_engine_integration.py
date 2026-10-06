import unittest
import os
import uuid
import random
from skills.market_portfolio_hedge_engine import (
    MarketPortfolioHedgeEngine,
    market_portfolio_hedge_engine_run
)
from skills.db_storage import db_storage_connect
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent_fetch
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine_calculate


class TestMarketPortfolioHedgeEngineIntegration(unittest.TestCase):

    def test_hedge_engine_integration_workflow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        balance = round(random.uniform(10000.0, 500000.0), 2)
        volatility = round(random.uniform(0.1, 0.9), 4)

        conn = db_storage_connect()
        self.assertIsNotNone(conn)

        collector_data = market_portfolio_collector_agent_fetch(portfolio_id)
        self.assertIsInstance(collector_data, dict)

        mc_metrics = market_portfolio_stress_monte_carlo_engine_calculate(portfolio_id, balance)
        self.assertIsInstance(mc_metrics, dict)

        engine = MarketPortfolioHedgeEngine()
        hedge_calc = engine.calculate_hedge_positions(portfolio_id)
        self.assertIn("hedge_size", hedge_calc)
        self.assertEqual(hedge_calc["asset"], portfolio_id)

        symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        payload = {"symbol": symbol, "size": hedge_calc["hedge_size"]}
        execution_res = engine.execute_hedge(payload)
        self.assertIn("order_id", execution_res)
        self.assertEqual(execution_res["symbol"], symbol)

        run_res = market_portfolio_hedge_engine_run(
            portfolio_id=portfolio_id,
            balance=balance,
            mc_metrics=mc_metrics,
            volatility=volatility
        )

        self.assertEqual(run_res["status"], "success")
        self.assertEqual(run_res["portfolio_id"], portfolio_id)
        self.assertIn("hedge_order_id", run_res)

        log_path = f"logs/hedge_{portfolio_id}.log"
        self.assertTrue(os.path.exists(log_path))

        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
            self.assertIn(portfolio_id, log_content)
            self.assertIn(str(balance), log_content)
            self.assertIn(str(volatility), log_content)


if __name__ == "__main__":
    unittest.main()