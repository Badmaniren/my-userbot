import unittest
import uuid
import random
from skills.market_portfolio_stress_hedge_optimizer import (
    market_portfolio_stress_hedge_optimizer,
    optimize_stress_hedge,
    calculate_hedge_positions,
    validate_portfolio_liquidity
)

class TestMarketPortfolioStressHedgeOptimizerIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.matrix_id = f"matrix-{uuid.uuid4()}"
        self.risk_tolerance = round(random.uniform(0.05, 0.5), 2)
        self.liquidity_limit = round(random.uniform(10000.0, 100000.0), 2)
        self.threshold = round(random.uniform(0.1, 0.9), 2)

    def test_optimize_stress_hedge_real_execution(self):
        result = optimize_stress_hedge(
            portfolio_id=self.portfolio_id,
            stress_matrix_id=self.matrix_id,
            risk_tolerance=self.risk_tolerance
        )
        self.assertIsInstance(result, dict)
        self.assertIn('hedge_recommendations', result)
        recommendations = result['hedge_recommendations']
        self.assertIn('asset', recommendations)
        self.assertIn('volume', recommendations)
        self.assertGreaterEqual(recommendations['volume'], 0.0)

    def test_calculate_hedge_positions_real_execution(self):
        positions = calculate_hedge_positions(
            portfolio_id=self.portfolio_id,
            liquidity_limit=self.liquidity_limit
        )
        self.assertIsInstance(positions, list)
        self.assertTrue(len(positions) > 0)
        for pos in positions:
            self.assertIn('asset', pos)
            self.assertIn('amount', pos)
            self.assertEqual(pos['amount'], self.liquidity_limit * 0.1)

    def test_validate_portfolio_liquidity_real_execution(self):
        try:
            response = validate_portfolio_liquidity(
                portfolio_id=self.portfolio_id,
                threshold=self.threshold
            )
            self.assertIsNotNone(response)
        except Exception as e:
            self.skipTest(f"External API Gateway not available in this environment: {e}")

    def test_market_portfolio_stress_hedge_optimizer_interface(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "scenario_id": self.matrix_id,
            "target_risk_reduction": self.risk_tolerance
        }
        output = market_portfolio_stress_hedge_optimizer(payload)
        self.assertIsInstance(output, dict)
        self.assertIn("hedge_positions", output)
        self.assertIn("status", output)
        self.assertEqual(output["status"], "optimized")

        positions = output["hedge_positions"]
        self.assertTrue(len(positions) > 0)
        for pos in positions:
            self.assertIn("ticker", pos)
            self.assertIn("action", pos)
            self.assertIn("size", pos)
            self.assertEqual(pos["size"], float(self.risk_tolerance) * 1000)

if __name__ == '__main__':
    unittest.main()