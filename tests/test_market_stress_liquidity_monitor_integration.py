import unittest
import uuid
import random
import os
import tempfile
from skills.market_stress_liquidity_monitor import (
    market_stress_liquidity_monitor,
    db_storage,
    market_portfolio_stress_scenario_pipeline,
    market_portfolio_var_liquidity_core,
    market_portfolio_slippage_model
)

class IntegrationTestMarketStressLiquidityMonitor(unittest.TestCase):
    def setUp(self):
        self.test_asset_id = f"ASSET_{uuid.uuid4().hex[:8]}"
        self.stress_level = round(random.uniform(1.5, 9.9), 2)
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_market_stress_liquidity_monitor_integration(self):
        db_connection = db_storage()
        
        pipeline_result = market_portfolio_stress_scenario_pipeline(
            asset_id=self.test_asset_id,
            intensity=self.stress_level
        )
        
        liquidity_core_metrics = market_portfolio_var_liquidity_core(
            asset_id=self.test_asset_id,
            scenario_data=pipeline_result
        )
        
        slippage_assessment = market_portfolio_slippage_model(
            metrics=liquidity_core_metrics
        )

        monitor_output = market_stress_liquidity_monitor(
            db=db_connection,
            asset_id=self.test_asset_id,
            stress_intensity=self.stress_level,
            slippage_data=slippage_assessment,
            export_path=self.temp_dir.name
        )

        self.assertIsNotNone(monitor_output)
        self.assertIn("status", monitor_output)
        self.assertEqual(monitor_output.get("asset_id"), self.test_asset_id)
        
        generated_files = os.listdir(self.temp_dir.name)
        self.assertTrue(
            len(generated_files) > 0,
            "Интеграционный тест не зафиксировал создание артефактов мониторинга ликвидности"
        )

if __name__ == "__main__":
    unittest.main()