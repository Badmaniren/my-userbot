import unittest
import uuid
import random
import os
from skills.market_portfolio_macro_liquidity_aggregator import (
    MarketPortfolioMacroLiquidityAggregator,
    market_portfolio_macro_liquidity_aggregator
)
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core


class TestMarketPortfolioMacroLiquidityAggregatorIntegration(unittest.TestCase):

    def test_end_to_end_macro_liquidity_aggregation(self):
        portfolio_id = str(uuid.uuid4())
        macro_liquidity_index = round(random.uniform(10.0, 1000.0), 4)
        stress_factor = round(random.uniform(0.0, 1.0), 4)
        audit_output_path = f"test_audit_{uuid.uuid4()}.txt"

        payload = {
            "portfolio_id": portfolio_id,
            "macro_liquidity_index": macro_liquidity_index,
            "stress_factor": stress_factor,
            "audit_output_path": audit_output_path
        }

        try:
            result = market_portfolio_macro_liquidity_aggregator(payload)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("status"), "success")
            expected_aggregated_id = f"agg_{portfolio_id}"
            self.assertEqual(result.get("aggregated_id"), expected_aggregated_id)

            self.assertTrue(os.path.exists(audit_output_path))
            with open(audit_output_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(portfolio_id, content)
                self.assertIn(str(macro_liquidity_index), content)
                self.assertIn(str(stress_factor), content)
                self.assertIn(expected_aggregated_id, content)

        finally:
            if os.path.exists(audit_output_path):
                os.remove(audit_output_path)

    def test_class_methods_integration(self):
        aggregator_instance = MarketPortfolioMacroLiquidityAggregator(
            db_storage=db_storage,
            market_portfolio_collector_agent=market_portfolio_collector_agent,
            market_portfolio_var_liquidity_core=market_portfolio_var_liquidity_core
        )

        token = f"TEST_TOKEN_{uuid.uuid4().hex[:8]}"
        collection_result = aggregator_instance.aggregate_macro_liquidity(token)
        self.assertIsNotNone(collection_result)

        stress_url = "https://httpbin.org/bytes/128"
        stress_value = aggregator_instance.compute_stress_index(stress_url)
        self.assertIsInstance(stress_value, float)
        self.assertGreater(stress_value, 0.0)

        anomaly_id = str(uuid.uuid4())
        anomaly_result = aggregator_instance.run_anomaly_pipeline(anomaly_id)
        self.assertIsInstance(anomaly_result, dict)

        export_path = f"test_export_{uuid.uuid4()}.log"
        export_result = aggregator_instance.export_audit_logs(export_path)
        self.assertIsInstance(export_result, str)


if __name__ == "__main__":
    unittest.main()