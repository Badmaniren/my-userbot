import unittest
import uuid
import random
from skills.market_portfolio_macro_liquidity_gate import MacroLiquidityGate, market_portfolio_macro_liquidity_gate
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core

class TestMacroLiquidityGateIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.base_liquidity = round(random.uniform(1000.0, 50000.0), 2)
        self.macro_factor = round(random.uniform(-5.0, 5.0), 2)
        
        self.gate_instance = MacroLiquidityGate(
            db_storage=db_storage,
            market_portfolio_var_liquidity_core=market_portfolio_var_liquidity_core
        )

    def test_market_portfolio_macro_liquidity_gate_function(self):
        input_data = {
            "portfolio_id": self.portfolio_id,
            "liquidity_data": {
                "base_liquidity": self.base_liquidity
            },
            "macro_factor": self.macro_factor
        }
        
        result = market_portfolio_macro_liquidity_gate(input_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("macro_factor"), self.macro_factor)
        
        expected_score = self.base_liquidity + self.macro_factor
        self.assertAlmostEqual(result.get("aggregated_score"), expected_score)
        self.assertIn("liquidity_data", result)

    def test_macro_liquidity_gate_class_aggregation(self):
        result = self.gate_instance.aggregate_macro_liquidity(self.portfolio_id)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("macro_liquidity_score", result)
        self.assertIn("details", result)
        self.assertIsInstance(result.get("macro_liquidity_score"), float)

if __name__ == "__main__":
    unittest.main()