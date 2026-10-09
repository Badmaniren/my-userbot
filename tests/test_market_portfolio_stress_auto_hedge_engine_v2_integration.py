import unittest
import uuid
import random

from skills.market_portfolio_stress_auto_hedge_engine_v2 import (
    market_portfolio_stress_auto_hedge_engine_v2,
)


class TestMarketPortfolioStressAutoHedgeEngineV2Integration(unittest.TestCase):

    def test_auto_hedge_engine_calculation(self):
        portfolio_id = str(uuid.uuid4())
        capital = round(random.uniform(10000.0, 1000000.0), 2)
        
        simulation_data = {
            "simulation_id": str(uuid.uuid4()),
            "risk_score": round(random.uniform(0.1, 0.9), 4),
            "max_drawdown": round(random.uniform(0.05, 0.5), 4)
        }

        result = market_portfolio_stress_auto_hedge_engine_v2(
            portfolio_id=portfolio_id,
            simulation_data=simulation_data,
            capital=capital
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("hedge_order"), "BUY")
        self.assertEqual(result.get("volume"), capital * 0.1)
        self.assertEqual(result.get("simulation_data"), simulation_data)


if __name__ == "__main__":
    unittest.main()