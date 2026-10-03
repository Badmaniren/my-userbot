import unittest
import uuid
import random
import os
from skills.market_portfolio_macro_liquidity_gate import market_portfolio_macro_liquidity_gate
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core

class TestMarketPortfolioMacroLiquidityGateIntegration(unittest.TestCase):
    def test_macro_liquidity_gate_integration_flow(self):
        unique_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        random_liquidity_factor = round(random.uniform(0.1, 99.9), 4)
        random_macro_index = random.randint(1000, 99999)

        collector_payload = {
            "portfolio_id": unique_portfolio_id,
            "liquidity_metric": random_liquidity_factor,
            "macro_index": random_macro_index,
            "status": "active"
        }

        collector_result = market_portfolio_collector_agent(collector_payload)
        self.assertIsNotNone(collector_result, "Collector agent must return data")

        var_core_input = {
            "portfolio_id": unique_portfolio_id,
            "base_liquidity": random_liquidity_factor
        }
        var_core_result = market_portfolio_var_liquidity_core(var_core_input)
        self.assertIn("portfolio_id", var_core_result)

        gate_input = {
            "portfolio_id": unique_portfolio_id,
            "liquidity_data": var_core_result,
            "macro_factor": random_macro_index
        }

        gate_output = market_portfolio_macro_liquidity_gate(gate_input)

        self.assertIsInstance(gate_output, dict, "Gate must return a structured dictionary")
        self.assertEqual(gate_output.get("portfolio_id"), unique_portfolio_id)
        self.assertEqual(gate_output.get("macro_factor"), random_macro_index)
        self.assertIn("aggregated_score", gate_output)

        db_payload = {
            "table": "macro_liquidity_gates",
            "record_id": unique_portfolio_id,
            "data": gate_output
        }
        db_storage_result = db_storage(db_payload)
        self.assertTrue(db_storage_result, "Database storage operation must succeed without suppression")

if __name__ == "__main__":
    unittest.main()