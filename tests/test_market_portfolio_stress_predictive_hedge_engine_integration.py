import unittest
import uuid
import random
import os
import json

from skills.market_portfolio_stress_predictive_hedge_engine import (
    MarketPortfolioStressPredictiveHedgeEngine,
    market_portfolio_stress_predictive_hedge_engine,
)
from skills.market_portfolio_stress_scenario_pipeline import (
    market_portfolio_stress_scenario_pipeline,
)
from skills.market_portfolio_stress_monte_carlo_engine import (
    market_portfolio_stress_monte_carlo_engine,
)
from skills.market_portfolio_stress_auto_rebalance_trigger import (
    market_portfolio_stress_auto_rebalance_trigger,
)
from skills.db_storage import db_storage


class RealDbStorageStub:
    def save_hedge_event(self, event_record):
        pass


class TestMarketPortfolioStressPredictiveHedgeEngineIntegration(unittest.TestCase):

    def test_predict_and_rebalance_integration(self):
        portfolio_id = str(uuid.uuid4())

        scenario_pipeline = market_portfolio_stress_scenario_pipeline()
        monte_carlo_engine = market_portfolio_stress_monte_carlo_engine()
        auto_rebalance_trigger = market_portfolio_stress_auto_rebalance_trigger()
        db_stub = RealDbStorageStub()

        engine = MarketPortfolioStressPredictiveHedgeEngine(
            db_storage=db_stub,
            market_portfolio_stress_scenario_pipeline=scenario_pipeline,
            market_portfolio_stress_monte_carlo_engine=monte_carlo_engine,
            market_portfolio_stress_auto_rebalance_trigger=auto_rebalance_trigger,
        )

        result = engine.predict_and_rebalance(portfolio_id)

        self.assertIn("status", result)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)

    def test_functional_wrapper_and_file_creation(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        random_asset_count = random.randint(1, 5)
        generated_hedges = [f"ASSET_{uuid.uuid4().hex[:4].upper()}" for _ in range(random_asset_count)]

        rebalance_plan = {
            "recommended_hedges": generated_hedges
        }

        output_filename = f"test_hedge_output_{uuid.uuid4()}.json"

        try:
            result = market_portfolio_stress_predictive_hedge_engine(
                portfolio_id=portfolio_id,
                rebalance_plan=rebalance_plan,
                output_path=output_filename
            )

            self.assertEqual(result.get("target_portfolio"), portfolio_id)
            self.assertEqual(result.get("hedge_assets"), generated_hedges)
            self.assertEqual(result.get("status"), "PREDICTED")

            self.assertTrue(os.path.exists(output_filename))
            with open(output_filename, "r") as f:
                file_data = json.load(f)
                self.assertEqual(file_data.get("target_portfolio"), portfolio_id)
                self.assertEqual(file_data.get("hedge_assets"), generated_hedges)
        finally:
            if os.path.exists(output_filename):
                os.remove(output_filename)


if __name__ == "__main__":
    unittest.main()