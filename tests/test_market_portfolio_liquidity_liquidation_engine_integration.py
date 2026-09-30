import unittest
import uuid
import random

from skills.market_portfolio_liquidity_liquidation_engine import market_portfolio_liquidity_liquidation_engine


class TestMarketPortfolioLiquidityLiquidationEngineIntegration(unittest.TestCase):

    def test_end_to_end_liquidation_processing(self):
        engine = market_portfolio_liquidity_liquidation_engine()

        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        target_asset = random.choice(["BTC", "ETH", "SOL", "USDT", "AVAX"])
        shock_multiplier = round(random.uniform(0.05, 0.5), 4)
        initial_valuation = round(random.uniform(5000.0, 150000.0), 2)

        payload = {
            "portfolio_id": portfolio_id,
            "target_asset": target_asset,
            "shock_multiplier": shock_multiplier,
            "valuation_snapshot": {
                "valuation": initial_valuation
            }
        }

        result = engine.process_liquidation(payload)

        self.assertIsInstance(result, dict)
        self.assertIn("liquidation_id", result)
        self.assertIsInstance(result["liquidation_id"], str)

        # Проверяем корректность генерации UUID
        try:
            uuid.UUID(result["liquidation_id"])
        except ValueError:
            self.fail("liquidation_id is not a valid UUID string")

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["target_asset"], target_asset)
        self.assertEqual(result["status"], "LIQUIDATED")

        expected_final_valuation = initial_valuation * (1 - shock_multiplier)
        self.assertAlmostEqual(result["final_valuation"], expected_final_valuation, places=4)

    def test_execute_liquidation_dynamic_calculation(self):
        engine = market_portfolio_liquidity_liquidation_engine()

        portfolio_id = f"port_exec_{uuid.uuid4().hex[:6]}"
        asset_ticker = random.choice(["AAPL", "TSLA", "MSFT"])
        volume = random.randint(10, 1000)
        liquidation_price = round(random.uniform(100.0, 2000.0), 2)

        res = engine.execute_liquidation(portfolio_id, asset_ticker, volume, liquidation_price)

        self.assertIsInstance(res, dict)
        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["asset"], asset_ticker)
        self.assertEqual(res["volume"], volume)
        self.assertEqual(res["initial_price"], liquidation_price)
        self.assertIn("final_price", res)
        self.assertIn("slippage", res)
        self.assertIsInstance(res["final_price"], float)


if __name__ == '__main__':
    unittest.main()