import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io
from skills import market_portfolio_liquidity_scenario_analyzer


class TestMarketPortfolioLiquidityScenarioAnalyzer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.export_target = f"{uuid.uuid4().hex}.json"
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = uuid.uuid4().hex[:6].upper()
        self.percentage = round(random.uniform(1.0, 15.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]

    def tearDown(self):
        for path in [self.export_target, self.storage_file]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
            export_dir = os.path.dirname(path)
            if export_dir and os.path.exists(export_dir):
                try:
                    os.rmdir(export_dir)
                except OSError:
                    pass

    def test_ensure_dir_exists(self):
        nested_dir = uuid.uuid4().hex
        file_name = uuid.uuid4().hex + ".json"
        target_path = os.path.join(nested_dir, file_name)
        
        market_portfolio_liquidity_scenario_analyzer._ensure_dir_exists(target_path)
        self.assertTrue(os.path.exists(nested_dir))
        
        try:
            os.rmdir(nested_dir)
        except OSError:
            pass

    def test_analyze_liquidity_stress_scenarios_execution(self):
        mock_var_val = round(random.uniform(100.0, 5000.0), 2)
        mock_impact_val = round(random.uniform(50.0, 6000.0), 2)

        mock_var_data = {"portfolio_id": self.portfolio_id, "var": mock_var_val}
        mock_stress_data = {"symbol": self.symbol, "impact": mock_impact_val}

        with patch("skills.market_portfolio_var_liquidity_core.calculate_var_liquidity", return_value=mock_var_data) as p1, \
             patch("skills.market_portfolio_stress_scenario_pipeline.run_stress_scenario_pipeline", return_value=mock_stress_data) as p2:
            
            result = market_portfolio_liquidity_scenario_analyzer.analyze_liquidity_stress_scenarios(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                export_target=self.export_target,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts,
                storage_file=self.storage_file
            )

            p1.assert_called_once_with(self.portfolio_id, self.confidence_level, self.export_target)
            p2.assert_called_once_with(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["var_liquidity_data"], mock_var_data)
            self.assertEqual(result["stress_pipeline_data"], mock_stress_data)
            
            expected_reserve = float(round(max(mock_var_val, mock_impact_val) * 1.15, 10))
            self.assertEqual(result["reserve_capital_requirement"], expected_reserve)
            self.assertEqual(result["capital_reserve_requirement"], expected_reserve)

            self.assertTrue(os.path.exists(self.export_target))
            self.assertTrue(os.path.exists(self.storage_file))

    def test_market_portfolio_liquidity_scenario_analyzer_class_execution(self):
        mock_var_val = round(random.uniform(200.0, 4000.0), 2)
        mock_stress_result = {"status": uuid.uuid4().hex, "impact": round(random.uniform(10.0, 1000.0), 2)}
        mock_var_result = {"portfolio_id": self.portfolio_id, "var": mock_var_val}

        class MockPipelineClass:
            def __init__(self, storage_path):
                self.storage_path = storage_path

            def execute(self, sym, pct, shf):
                return mock_stress_result

        with patch("skills.market_portfolio_var_liquidity_core.calculate_var_liquidity", return_value=mock_var_result) as p1, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline", MockPipelineClass):
            
            analyzer = market_portfolio_liquidity_scenario_analyzer.MarketPortfolioLiquidityScenarioAnalyzer(storage_file=self.storage_file)
            evaluation = analyzer.evaluate_portfolio(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                export_target=self.export_target,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            p1.assert_called_once_with(self.portfolio_id, self.confidence_level, self.export_target)
            self.assertEqual(evaluation["portfolio_id"], self.portfolio_id)
            self.assertEqual(evaluation["var_result"], mock_var_result)
            self.assertEqual(evaluation["stress_result"], mock_stress_result)


if __name__ == "__main__":
    unittest.main()