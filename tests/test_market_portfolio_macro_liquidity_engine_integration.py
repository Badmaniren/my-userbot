import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_macro_liquidity_engine import market_portfolio_macro_liquidity_engine
from skills.db_storage import db_storage
from skills.market_portfolio_integration_hub import market_portfolio_integration_hub
from skills.market_portfolio_monitor import market_portfolio_monitor

class TestMarketPortfolioMacroLiquidityEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_portfolio_id = str(uuid.uuid4())
        self.test_macro_factor = f"CPI_{random.randint(100, 999)}_{uuid.uuid4().hex[:6]}"
        self.test_liquidity_threshold = round(random.uniform(10000.0, 500000.0), 2)

    def test_macro_liquidity_pipeline_real_execution(self):
        input_payload = {
            "portfolio_id": self.test_portfolio_id,
            "macro_factor": self.test_macro_factor,
            "liquidity_threshold": self.test_liquidity_threshold,
            "metric_value": round(random.uniform(1.5, 9.9), 4)
        }

        integration_result = market_portfolio_integration_hub(
            target_module="macro_liquidity_engine",
            payload=input_payload
        )
        self.assertIsNotNone(integration_result)

        engine_output = market_portfolio_macro_liquidity_engine(input_payload)

        self.assertIsInstance(engine_output, dict)
        self.assertIn("status", engine_output)
        self.assertEqual(engine_output.get("portfolio_id"), self.test_portfolio_id)
        self.assertEqual(engine_output.get("macro_factor"), self.test_macro_factor)
        self.assertIn("liquidity_score", engine_output)

        stored_data = db_storage(
            action="get_macro_liquidity_record",
            portfolio_id=self.test_portfolio_id
        )
        self.assertIsNotNone(stored_data)
        self.assertEqual(stored_data.get("macro_factor"), self.test_macro_factor)
        self.assertEqual(stored_data.get("liquidity_threshold"), self.test_liquidity_threshold)

        monitor_check = market_portfolio_monitor(
            portfolio_id=self.test_portfolio_id,
            mode="macro_liquidity_validation"
        )
        self.assertTrue(monitor_check.get("is_healthy", False))

if __name__ == "__main__":
    unittest.main()