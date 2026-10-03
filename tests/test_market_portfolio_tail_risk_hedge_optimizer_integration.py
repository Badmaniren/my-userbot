import unittest
import uuid
import random
from skills.market_portfolio_tail_risk_hedge_optimizer import (
    market_portfolio_tail_risk_hedge_optimizer,
    optimize_tail_risk_hedges,
    TailRiskHedgeOptimizerException
)

class TestMarketPortfolioTailRiskHedgeOptimizerIntegration(unittest.TestCase):
    def test_tail_risk_hedge_optimizer_integration(self):
        portfolio_id = f"test-portfolio-{uuid.uuid4()}"
        confidence = round(random.uniform(0.90, 0.99), 2)

        payload = {
            "portfolio_id": portfolio_id,
            "confidence_level": confidence,
            "stress_data": {
                "shock_factor": random.choice([-0.1, -0.2, -0.3])
            }
        }

        try:
            result = market_portfolio_tail_risk_hedge_optimizer(payload)
            self.assertIsInstance(result, dict)
            self.assertIn("optimal_hedges", result)
            self.assertIn("expected_tail_loss_reduction", result)
            self.assertIn("simulation_data", result)
            self.assertIn("stress_matrix", result)
        except Exception as e:
            self.fail(f"Integration execution failed with error: {e}")

    def test_optimize_tail_risk_hedges_exception_flow(self):
        invalid_portfolio_id = f"nonexistent-{uuid.uuid4()}"
        with self.assertRaises(TailRiskHedgeOptimizerException):
            optimize_tail_risk_hedges(portfolio_id=invalid_portfolio_id, confidence=0.95)

if __name__ == "__main__":
    unittest.main()