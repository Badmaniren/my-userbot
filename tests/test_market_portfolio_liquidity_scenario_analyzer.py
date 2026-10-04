import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import tempfile
from skills import market_portfolio_liquidity_scenario_analyzer

class TestMarketPortfolioLiquidityScenarioAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4().hex)
        self.symbol = str(uuid.uuid4().hex[:6]).upper()
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        self.confidence_level = round(random.uniform(0.9, 0.99), 2)
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.export_target = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        self.storage_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ensure_dir_exists_local_path(self):
        random_sub = uuid.uuid4().hex
        random_file = f"{uuid.uuid4().hex}.json"
        target = os.path.join(self.temp_dir.name, random_sub, random_file)
        
        market_portfolio_liquidity_scenario_analyzer._ensure_dir_exists(target)
        self.assertTrue(os.path.exists(os.path.dirname(target)))

    def test_ensure_dir_exists_s3_path(self):
        s3_path = f"s3://{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        try:
            market_portfolio_liquidity_scenario_analyzer._ensure_dir_exists(s3_path)
        except Exception as e:
            self.fail(f"_ensure_dir_exists failed on s3 path: {e}")

    def test_analyze_liquidity_stress_scenarios_logic(self):
        mock_var_val = round(random.uniform(100.0, 5000.0), 2)
        mock_impact = round(random.uniform(100.0, 5000.0), 2)
        expected_reserve = float(round(max(mock_var_val, mock_impact) * 1.15, 10))

        with patch('skills.market_portfolio_var_liquidity_core.calculate_var_and_liquidity') as mock_calc, \
             patch('skills.market_portfolio_stress_scenario_pipeline.run_stress_scenario_pipeline') as mock_pipeline:
            
            mock_calc.return_value = {"var": mock_var_val, "portfolio_id": self.portfolio_id}
            mock_pipeline.return_value = {"impact": mock_impact, "symbol": self.symbol}

            result = market_portfolio_liquidity_scenario_analyzer.analyze_liquidity_stress_scenarios(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                export_target=self.export_target,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts,
                storage_file=self.storage_file
            )

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["reserve_capital_requirement"], expected_reserve)
            self.assertEqual(result["capital_reserve_requirement"], expected_reserve)
            self.assertEqual(result["var_liquidity_data"]["var"], mock_var_val)
            self.assertEqual(result["stress_pipeline_data"]["impact"], mock_impact)

            self.assertTrue(os.path.exists(self.export_target))
            self.assertTrue(os.path.exists(self.storage_file))

            with open(self.export_target, 'r') as f:
                saved_var_data = json.load(f)
            self.assertEqual(saved_var_data["var"], mock_var_val)

            with open(self.storage_file, 'r') as f:
                saved_stress_data = json.load(f)
            self.assertEqual(saved_stress_data["impact"], mock_impact)

    def test_market_portfolio_liquidity_scenario_analyzer_class(self):
        mock_var_val = round(random.uniform(1000.0, 10000.0), 2)
        mock_impact = round(random.uniform(1000.0, 10000.0), 2)

        with patch('skills.market_portfolio_var_liquidity_core.calculate_var_and_liquidity') as mock_calc, \
             patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline') as mock_pipeline_cls:
            
            mock_calc.return_value = {"var": mock_var_val}
            
            mock_pipeline_instance = mock_pipeline_cls.return_value
            mock_pipeline_instance.execute.return_value = {"impact": mock_impact}

            analyzer = market_portfolio_liquidity_scenario_analyzer.MarketPortfolioLiquidityScenarioAnalyzer(
                storage_file=self.storage_file
            )

            calculated_reserve = analyzer._calculate_required_reserve(mock_var_val, mock_impact)
            expected_reserve = float(round(max(mock_var_val, mock_impact) * 1.15, 10))
            self.assertEqual(calculated_reserve, expected_reserve)

            eval_result = analyzer.evaluate_portfolio(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                export_target=self.export_target,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(eval_result["portfolio_id"], self.portfolio_id)
            self.assertEqual(eval_result["var_result"]["var"], mock_var_val)
            self.assertEqual(eval_result["stress_result"]["impact"], mock_impact)
            
            mock_pipeline_cls.assert_called_once_with(self.storage_file)
            mock_pipeline_instance.execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)

if __name__ == '__main__':
    unittest.main()