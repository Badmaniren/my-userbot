import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_liquidity_risk_evaluator import (
    MarketPortfolioLiquidityRiskEvaluator,
    evaluate_liquidity_risk,
    evaluate_liquidity_risk_assessment
)

class TestMarketPortfolioLiquidityRiskEvaluatorIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.symbol = random.choice(["AAPL", "BTC", "ETH", "TSLA", "SBER"])
        self.percentage = round(random.uniform(1.0, 25.0), 2)
        self.shifts = [round(random.uniform(-0.15, -0.01), 4), round(random.uniform(0.01, 0.15), 4)]
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        self.export_target = f"test_export_{uuid.uuid4()}.json"

    def tearDown(self):
        for file_path in [self.storage_file, self.export_target]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def test_evaluator_class_comprehensive_risk(self):
        evaluator = MarketPortfolioLiquidityRiskEvaluator(storage_file=self.storage_file)
        result = evaluator.evaluate_comprehensive_risk(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_target,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("evaluated_portfolio"), self.portfolio_id)
        self.assertIn("scenario_output", result)
        self.assertIn("var_output", result)

    def test_evaluate_liquidity_risk_function(self):
        result = evaluate_liquidity_risk(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_target,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts,
            storage_file=self.storage_file
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("scenario_analysis", result)
        self.assertIn("var_liquidity_calculation", result)

    def test_evaluate_liquidity_risk_assessment_with_export(self):
        self.assertFalse(os.path.exists(self.export_target))

        result = evaluate_liquidity_risk_assessment(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_target,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts,
            storage_file=self.storage_file
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("scenario_analysis", result)
        self.assertIn("var_liquidity_core", result)

        self.assertTrue(os.path.exists(self.export_target), "Export target file must be created")

        with open(self.export_target, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data.get("portfolio_id"), self.portfolio_id)
            self.assertIn("scenario_analysis", data)
            self.assertIn("var_liquidity_core", data)

if __name__ == "__main__":
    unittest.main()