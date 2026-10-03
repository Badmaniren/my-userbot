import unittest
import os
import uuid
import random
from skills.market_portfolio_liquidity_stress_evaluator import evaluate_liquidity_stress_losses
from skills.market_portfolio_var_liquidity_core import calculate_var_and_liquidity
from skills.market_portfolio_stress_scenario_pipeline import run_stress_scenario_pipeline

class TestMarketPortfolioLiquidityStressEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.symbol = f"SYM{random.randint(100, 999)}"
        self.confidence_level = round(random.uniform(0.95, 0.99), 4)
        self.percentage = round(random.uniform(5.0, 25.0), 2)
        self.shifts = [round(random.uniform(-0.1, -0.01), 4), round(random.uniform(-0.2, -0.05), 4)]
        self.export_target = f"test_export_{uuid.uuid4().hex[:6]}.json"
        self.storage_file = f"test_storage_{uuid.uuid4().hex[:6]}.json"

    def tearDown(self):
        for filename in [self.export_target, self.storage_file]:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except OSError:
                    pass

    def test_liquidity_stress_evaluator_integration(self):
        var_liquidity_result = calculate_var_and_liquidity(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_target
        )
        self.assertIsNotNone(var_liquidity_result)

        stress_pipeline_result = run_stress_scenario_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )
        self.assertIsNotNone(stress_pipeline_result)

        evaluation_output = evaluate_liquidity_stress_losses(
            portfolio_id=self.portfolio_id,
            symbol=self.symbol,
            confidence_level=self.confidence_level,
            percentage=self.percentage,
            shifts=self.shifts,
            export_target=self.export_target,
            storage_file=self.storage_file
        )

        self.assertIsInstance(evaluation_output, dict)
        self.assertIn("total_losses", evaluation_output)
        self.assertIn("portfolio_id", evaluation_output)
        self.assertEqual(evaluation_output["portfolio_id"], self.portfolio_id)
        
        self.assertTrue(os.path.exists(self.export_target))
        self.assertTrue(os.path.exists(self.storage_file))

if __name__ == "__main__":
    unittest.main()