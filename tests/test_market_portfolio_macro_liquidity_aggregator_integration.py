import unittest
import uuid
import random
import os
from skills.market_portfolio_macro_liquidity_aggregator import (
    market_portfolio_macro_liquidity_aggregator,
)
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core


class TestMarketPortfolioMacroLiquidityAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.test_macro_index = round(random.uniform(100.0, 1000.0), 4)
        self.test_stress_factor = round(random.uniform(0.01, 0.99), 4)
        self.export_filepath = f"macro_agg_audit_{uuid.uuid4().hex}.log"

    def tearDown(self):
        if os.path.exists(self.export_filepath):
            try:
                os.remove(self.export_filepath)
            except OSError:
                pass

    def test_macro_liquidity_aggregation_pipeline(self):
        collector_payload = {
            "portfolio_id": self.test_portfolio_id,
            "macro_liquidity_index": self.test_macro_index,
            "stress_factor": self.test_stress_factor,
            "timestamp": uuid.uuid1().urn
        }
        
        collector_result = market_portfolio_collector_agent(collector_payload)
        self.assertIsNotNone(collector_result)

        var_core_input = {
            "portfolio_id": self.test_portfolio_id,
            "liquidity_adjustment": self.test_macro_index
        }
        var_core_result = market_portfolio_var_liquidity_core(var_core_input)
        self.assertIsNotNone(var_core_result)

        aggregator_input = {
            "portfolio_id": self.test_portfolio_id,
            "macro_liquidity_index": self.test_macro_index,
            "stress_factor": self.test_stress_factor,
            "collector_data": collector_result,
            "var_core_data": var_core_result,
            "audit_output_path": self.export_filepath
        }

        aggregator_response = market_portfolio_macro_liquidity_aggregator(aggregator_input)

        self.assertIsInstance(aggregator_response, dict)
        self.assertIn("aggregated_id", aggregator_response)
        
        returned_id = aggregator_response["aggregated_id"]
        self.assertIsInstance(returned_id, str)
        self.assertTrue(len(returned_id) > 0)

        db_record = db_storage({"action": "get", "portfolio_id": self.test_portfolio_id})
        self.assertIsNotNone(db_record)

        self.assertTrue(
            os.path.exists(self.export_filepath),
            "Интеграционный модуль не создал реальный файл аудита макропоказателей ликвидности"
        )
        
        with open(self.export_filepath, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(str(self.test_portfolio_id), file_content)
            self.assertIn(str(self.test_macro_index), file_content)


if __name__ == "__main__":
    unittest.main()