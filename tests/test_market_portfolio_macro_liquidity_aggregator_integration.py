import unittest
import uuid
import os
import random
from skills.market_portfolio_macro_liquidity_aggregator import market_portfolio_macro_liquidity_aggregator

class TestMarketPortfolioMacroLiquidityAggregatorIntegration(unittest.TestCase):
    def test_aggregate_macro_liquidity_integration(self):
        portfolio_id = str(uuid.uuid4())
        context = f"context_{random.randint(1000, 9999)}"
        liquidity_data = {"volume": random.uniform(1000.0, 50000.0), "ratio": random.random()}
        export_path = f"macro_liquidity_test_{uuid.uuid4()}.json"

        try:
            result = market_portfolio_macro_liquidity_aggregator.aggregate_macro_liquidity(
                portfolio_id=portfolio_id,
                context=context,
                liquidity_data=liquidity_data,
                export_path=export_path
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["context"], context)
            self.assertEqual(result["liquidity_data"], liquidity_data)

            self.assertTrue(os.path.exists(export_path))
            with open(export_path, "r") as f:
                file_content = f.read()
                self.assertIn(portfolio_id, file_content)
        finally:
            if os.path.exists(export_path):
                os.remove(export_path)

if __name__ == "__main__":
    unittest.main()