import unittest
import uuid
import random

from skills.market_portfolio_liquidity_impact_evaluator import (
    MarketPortfolioLiquidityImpactEvaluator,
    market_portfolio_liquidity_impact_evaluator
)
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.db_storage import db_storage


class TestMarketPortfolioLiquidityImpactEvaluatorIntegration(unittest.TestCase):

    def test_end_to_end_liquidity_evaluation(self):
        rand_suffix = uuid.uuid4().hex[:6]
        test_portfolio_id = f"port_integ_{rand_suffix}"
        test_asset = f"TKN_{rand_suffix.upper()}"
        test_volume = float(random.randint(5000, 50000))

        payload = {
            "portfolio_id": test_portfolio_id,
            "asset_symbol": test_asset,
            "order_volume": test_volume
        }

        result = market_portfolio_liquidity_impact_evaluator(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), test_portfolio_id)
        self.assertEqual(result.get("asset_symbol"), test_asset)
        self.assertEqual(result.get("order_volume"), test_volume)
        self.assertEqual(result.get("status"), "evaluated")

        expected_impact = round(test_volume * 0.00002, 4)
        self.assertEqual(result.get("impact_score"), expected_impact)

        collected_data = result.get("collected_market_data")
        self.assertIsInstance(collected_data, dict)

        evaluator_class_instance = MarketPortfolioLiquidityImpactEvaluator(
            db_storage=db_storage
        )

        eval_res = evaluator_class_instance.evaluate_impact(test_asset, test_volume)
        self.assertIn("id", eval_res)
        self.assertEqual(eval_res.get("token"), test_asset)
        self.assertEqual(eval_res.get("impact"), test_volume * 0.00001)

        zones = evaluator_class_instance.detect_price_failure_zones(threshold=test_volume * 0.001)
        self.assertIsInstance(zones, list)
        self.assertTrue(len(zones) > 0)
        self.assertIn("zone_id", zones[0])

        penalty = evaluator_class_instance.calculate_execution_penalty(
            transaction_id=str(uuid.uuid4()),
            order_size=test_volume
        )
        self.assertIn("estimated_cost", penalty)
        self.assertEqual(penalty.get("estimated_cost"), test_volume * 0.0015)


if __name__ == "__main__":
    unittest.main()