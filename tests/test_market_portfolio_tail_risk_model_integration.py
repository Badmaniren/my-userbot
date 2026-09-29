import unittest
import uuid
import random
import os
from skills.market_portfolio_tail_risk_model import (
    calculate_tail_risk,
    TailRiskConfig
)
from skills.db_storage import save_portfolio_data, get_portfolio_data
from skills.market_portfolio_collector_agent import collect_market_data

class TestMarketPortfolioTailRiskModelIntegration(unittest.TestCase):
    def test_tail_risk_calculation_pipeline(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        asset_count = random.randint(3, 10)

        raw_market_data = {
            "portfolio_id": portfolio_id,
            "assets": [
                {
                    "ticker": f"TICK_{uuid.uuid4().hex[:4].upper()}",
                    "weight": round(1.0 / asset_count, 4),
                    "historical_returns": [round(random.gauss(-0.001, 0.02), 6) for _ in range(50)]
                }
                for _ in range(asset_count)
            ]
        }

        collected_data = collect_market_data(raw_market_data)
        self.assertIsNotNone(collected_data)

        db_saved = save_portfolio_data(portfolio_id, collected_data)
        self.assertTrue(db_saved)

        retrieved_data = get_portfolio_data(portfolio_id)
        self.assertEqual(retrieved_data["portfolio_id"], portfolio_id)

        confidence_level = round(random.uniform(0.95, 0.99), 2)
        config = TailRiskConfig(confidence=confidence_level, simulation_runs=random.randint(100, 1000))

        risk_metrics = calculate_tail_risk(retrieved_data, config)

        self.assertIn("var", risk_metrics)
        self.assertIn("expected_shortfall", risk_metrics)
        self.assertIsInstance(risk_metrics["var"], float)
        self.assertIsInstance(risk_metrics["expected_shortfall"], float)
        self.assertLess(risk_metrics["var"], 0.0)
        self.assertLess(risk_metrics["expected_shortfall"], risk_metrics["var"])

if __name__ == "__main__":
    unittest.main()