import unittest
import uuid
import random
import os
import tempfile
from skills.market_macro_liquidity_bridge import (
    MarketMacroLiquidityBridge,
    MacroLiquidityInput,
    PortfolioStressContext
)
from skills.db_storage import DBStorage
from skills.market_portfolio_stress_scenario_pipeline import MarketPortfolioStressScenarioPipeline
from skills.market_portfolio_var_liquidity_core import MarketPortfolioVarLiquidityCore

class TestMarketMacroLiquidityBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.db_path = tempfile.mktemp(suffix=".db")
        self.db_storage = DBStorage(connection_string=self.db_path)
        self.stress_pipeline = MarketPortfolioStressScenarioPipeline(db_storage=self.db_storage)
        self.var_liquidity_core = MarketPortfolioVarLiquidityCore(db_storage=self.db_storage)

        self.bridge = MarketMacroLiquidityBridge(
            db_storage=self.db_storage,
            stress_pipeline=self.stress_pipeline,
            var_liquidity_core=self.var_liquidity_core
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_macro_liquidity_integration_pipeline(self):
        random_portfolio_id = str(uuid.uuid4())
        random_scenario_id = str(uuid.uuid4())

        mock_liquidity_score = round(random.uniform(0.0, 100.0), 4)
        mock_macro_rate = round(random.uniform(-5.0, 15.0), 4)
        mock_cash_flow = round(random.uniform(10000.0, 10000000.0), 2)

        input_data = MacroLiquidityInput(
            portfolio_id=random_portfolio_id,
            scenario_id=random_scenario_id,
            liquidity_score=mock_liquidity_score,
            macro_interest_rate=mock_macro_rate,
            net_cash_flow=mock_cash_flow
        )

        integration_result = self.bridge.process_and_evaluate(input_data)

        self.assertIsNotNone(integration_result)
        self.assertEqual(integration_result.portfolio_id, random_portfolio_id)
        self.assertEqual(integration_result.scenario_id, random_scenario_id)

        stored_record = self.db_storage.get_macro_liquidity_record(random_portfolio_id)
        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record["liquidity_score"], mock_liquidity_score)
        self.assertEqual(stored_record["macro_interest_rate"], mock_macro_rate)

        stress_evaluation = self.stress_pipeline.evaluate_scenario(random_scenario_id)
        self.assertIsNotNone(stress_evaluation)
        self.assertTrue(stress_evaluation.is_processed)

        var_result = self.var_liquidity_core.calculate_var(random_portfolio_id)
        self.assertIsNotNone(var_result)
        self.assertGreaterEqual(var_result.var_value, 0.0)

if __name__ == "__main__":
    unittest.main()