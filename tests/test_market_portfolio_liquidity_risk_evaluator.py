import unittest
from unittest.mock import patch
import uuid
import random
import os
import io
import json
from skills.market_portfolio_liquidity_risk_evaluator import (
    MarketPortfolioLiquidityRiskEvaluator,
    evaluate_liquidity_risk,
    evaluate_liquidity_risk_assessment
)

class TestMarketPortfolioLiquidityRiskEvaluator(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.confidence_level = round(random.uniform(0.9, 0.99), 4)
        self.export_target = f"{uuid.uuid4().hex}.json"
        self.symbol = str(uuid.uuid4()).upper()[:5]
        self.percentage = round(random.uniform(1.0, 15.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(random.randint(2, 5))]
        self.storage_file = f"{uuid.uuid4().hex}.db"

    def tearDown(self):
        if os.path.exists(self.export_target):
            try:
                os.remove(self.export_target)
            except OSError:
                pass
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_class_based_evaluator_composition(self):
        mock_scenario_result = {
            "portfolio_id": self.portfolio_id,
            "status": uuid.uuid4().hex,
            "metric": random.random()
        }
        mock_var_result = {
            "var": random.random(),
            "liquidity_adjustment": random.random()
        }

        with patch("skills.market_portfolio_liquidity_risk_evaluator.MarketPortfolioLiquidityScenarioAnalyzer") as MockAnalyzer, \
             patch("skills.market_portfolio_liquidity_risk_evaluator.market_portfolio_var_liquidity_core") as MockVarCore:

            instance_analyzer = MockAnalyzer.return_value
            instance_analyzer.evaluate_portfolio.return_value = mock_scenario_result

            instance_var = MockVarCore.return_value
            instance_var.calculate_var_and_liquidity.return_value = mock_var_result

            evaluator = MarketPortfolioLiquidityRiskEvaluator(self.storage_file)
            result = evaluator.evaluate_comprehensive_risk(
                self.portfolio_id,
                self.confidence_level,
                self.export_target,
                self.symbol,
                self.percentage,
                self.shifts
            )

            MockAnalyzer.assert_called_once_with(self.storage_file)
            instance_analyzer.evaluate_portfolio.assert_called_once_with(
                self.portfolio_id,
                self.confidence_level,
                self.export_target,
                self.symbol,
                self.percentage,
                self.shifts
            )
            MockVarCore.assert_called_once()
            instance_var.calculate_var_and_liquidity.assert_called_once_with(
                self.portfolio_id,
                self.confidence_level,
                self.export_target
            )

            self.assertEqual(result["evaluated_portfolio"], self.portfolio_id)
            self.assertEqual(result["scenario_output"], mock_scenario_result)
            self.assertEqual(result["var_output"], mock_var_result)

    def test_functional_composition_standalone(self):
        mock_scenario_result = {
            "token": uuid.uuid4().hex,
            "stress_test": random.choice([True, False])
        }
        mock_var_result = {
            "liquidity_var": random.uniform(100.0, 5000.0)
        }

        with patch("skills.market_portfolio_liquidity_risk_evaluator.MarketPortfolioLiquidityScenarioAnalyzer") as MockAnalyzer, \
             patch("skills.market_portfolio_liquidity_risk_evaluator.market_portfolio_var_liquidity_core") as MockVarCore:

            instance_analyzer = MockAnalyzer.return_value
            instance_analyzer.evaluate_portfolio.return_value = mock_scenario_result

            instance_var = MockVarCore.return_value
            instance_var.calculate_var_and_liquidity.return_value = mock_var_result

            result = evaluate_liquidity_risk(
                self.portfolio_id,
                self.confidence_level,
                self.export_target,
                self.symbol,
                self.percentage,
                self.shifts,
                self.storage_file
            )

            MockAnalyzer.assert_called_once_with(self.storage_file)
            instance_analyzer.evaluate_portfolio.assert_called_once_with(
                self.portfolio_id,
                self.confidence_level,
                self.export_target,
                self.symbol,
                self.percentage,
                self.shifts
            )
            MockVarCore.assert_called_once()
            instance_var.calculate_var_and_liquidity.assert_called_once_with(
                self.portfolio_id,
                self.confidence_level,
                self.export_target
            )

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["scenario_analysis"], mock_scenario_result)
            self.assertEqual(result["var_liquidity_calculation"], mock_var_result)

    def test_functional_composition_io_handling(self):
        mock_scenario_result = {
            "id": uuid.uuid4().hex,
            "impact": random.randint(10, 100)
        }
        mock_var_result = {
            "core_score": random.random()
        }

        with patch("skills.market_portfolio_liquidity_risk_evaluator.MarketPortfolioLiquidityScenarioAnalyzer") as MockAnalyzer, \
             patch("skills.market_portfolio_liquidity_risk_evaluator.market_portfolio_var_liquidity_core") as MockVarCore, \
             patch("os.path.exists", return_value=False) as mock_exists, \
             patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file:

            instance_analyzer = MockAnalyzer.return_value
            instance_analyzer.evaluate_portfolio.return_value = mock_scenario_result

            instance_var = MockVarCore.return_value
            instance_var.calculate_var_and_liquidity.return_value = mock_var_result

            result = evaluate_liquidity_risk_assessment(
                self.portfolio_id,
                self.confidence_level,
                self.export_target,
                self.symbol,
                self.percentage,
                self.shifts,
                self.storage_file
            )

            mock_exists.assert_called_once_with(self.export_target)
            mock_file.assert_called_once_with(self.export_target, "w", encoding="utf-8")

            write_calls = [c for c in mock_file.mock_calls if c[0].endswith("write")]
            written_content = "".join(call.args[0] for call in write_calls)
            parsed_json = json.loads(written_content)

            self.assertEqual(parsed_json["portfolio_id"], self.portfolio_id)
            self.assertEqual(parsed_json["scenario_analysis"], mock_scenario_result)
            self.assertEqual(parsed_json["var_liquidity_core"], mock_var_result)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)

    def test_functional_composition_io_handling_file_exists(self):
        mock_scenario_result = {
            "msg": uuid.uuid4().hex
        }
        mock_var_result = {
            "val": random.random()
        }

        with patch("skills.market_portfolio_liquidity_risk_evaluator.MarketPortfolioLiquidityScenarioAnalyzer") as MockAnalyzer, \
             patch("skills.market_portfolio_liquidity_risk_evaluator.market_portfolio_var_liquidity_core") as MockVarCore, \
             patch("os.path.exists", return_value=True) as mock_exists, \
             patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file:

            instance_analyzer = MockAnalyzer.return_value
            instance_analyzer.evaluate_portfolio.return_value = mock_scenario_result

            instance_var = MockVarCore.return_value
            instance_var.calculate_var_and_liquidity.return_value = mock_var_result

            evaluate_liquidity_risk_assessment(
                self.portfolio_id,
                self.confidence_level,
                self.export_target,
                self.symbol,
                self.percentage,
                self.shifts,
                self.storage_file
            )

            mock_exists.assert_called_once_with(self.export_target)
            mock_file.assert_not_called()

if __name__ == "__main__":
    unittest.main()