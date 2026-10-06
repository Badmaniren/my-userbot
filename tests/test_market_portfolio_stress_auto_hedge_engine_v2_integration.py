import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_auto_hedge_engine_v2 import market_portfolio_stress_auto_hedge_engine_v2_run
from skills.db_storage import db_storage_connect, db_storage_save_portfolio, db_storage_get_hedge_result
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator_execute
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core_calculate

class TestMarketPortfolioStressAutoHedgeEngineV2(unittest.TestCase):

    def test_integration_stress_auto_hedge_pipeline(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        asset_symbol = f"ASSET_{random.choice(['BTC', 'ETH', 'SPY', 'GOLD'])}"
        initial_value = round(random.uniform(50000.0, 500000.0), 2)
        stress_drop_pct = round(random.uniform(10.0, 45.0), 2)

        db_conn = db_storage_connect()
        self.assertIsNotNone(db_conn)

        portfolio_data = {
            "portfolio_id": portfolio_id,
            "asset": asset_symbol,
            "value": initial_value,
            "status": "active"
        }
        saved_status = db_storage_save_portfolio(db_conn, portfolio_data)
        self.assertTrue(saved_status)

        simulation_result = market_portfolio_scenario_simulator_execute(portfolio_id, stress_drop_pct)
        self.assertIn("simulated_drawdown", simulation_result)

        var_metrics = market_portfolio_var_liquidity_core_calculate(portfolio_id)
        self.assertIn("var_value", var_metrics)

        hedge_action = market_portfolio_stress_auto_hedge_engine_v2_run(
            portfolio_id=portfolio_id,
            drop_scenario=stress_drop_pct,
            simulation_context=simulation_result,
            var_context=var_metrics
        )

        self.assertIsInstance(hedge_action, dict)
        self.assertEqual(hedge_action.get("portfolio_id"), portfolio_id)
        self.assertIn("hedge_order_id", hedge_action)
        self.assertGreater(hedge_action.get("hedge_amount", 0.0), 0.0)

        persisted_hedge = db_storage_get_hedge_result(db_conn, portfolio_id)
        self.assertEqual(persisted_hedge.get("hedge_order_id"), hedge_action.get("hedge_order_id"))

if __name__ == "__main__":
    unittest.main()