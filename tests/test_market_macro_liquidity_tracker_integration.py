import unittest
import uuid
import random
import os

from skills.market_macro_liquidity_tracker import (
    track_macro_liquidity,
    MacroLiquidityTrackerConfig
)
from skills.db_storage import DBStorage
from skills.market_portfolio_var_liquidity_core import LiquidityCore
from skills.market_portfolio_stress_scenario_pipeline import StressScenarioPipeline


class TestMarketMacroLiquidityTrackerIntegration(unittest.TestCase):

    def setUp(self):
        self.run_id = str(uuid.uuid4())
        self.db_path = f"test_macro_liquidity_{self.run_id}.db"
        self.db_storage = DBStorage(db_path=self.db_path)
        self.liquidity_core = LiquidityCore(storage=self.db_storage)
        self.stress_pipeline = StressScenarioPipeline(storage=self.db_storage)

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_macro_liquidity_pipeline_integration(self):
        test_rate = round(random.uniform(0.01, 0.08), 4)
        test_volume = random.randint(100000000, 999999999)

        config = MacroLiquidityTrackerConfig(
            tracking_id=self.run_id,
            interest_rate=test_rate,
            market_volume=test_volume,
            enable_persistence=True
        )

        tracking_result = track_macro_liquidity(
            config=config,
            db_storage=self.db_storage,
            liquidity_core=self.liquidity_core,
            stress_pipeline=self.stress_pipeline
        )

        self.assertIsNotNone(tracking_result)
        self.assertEqual(tracking_result.get("tracking_id"), self.run_id)
        self.assertEqual(tracking_result.get("interest_rate"), test_rate)
        self.assertEqual(tracking_result.get("market_volume"), test_volume)

        stored_data = self.db_storage.get_macro_liquidity(self.run_id)
        self.assertIsNotNone(stored_data)
        self.assertEqual(stored_data["tracking_id"], self.run_id)
        self.assertEqual(stored_data["interest_rate"], test_rate)
        self.assertEqual(stored_data["market_volume"], test_volume)

        core_metrics = self.liquidity_core.get_metrics_by_id(self.run_id)
        self.assertIsNotNone(core_metrics)
        self.assertIn("liquidity_score", core_metrics)


if __name__ == "__main__":
    unittest.main()