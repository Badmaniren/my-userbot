import os
import json
import uuid
import random
import unittest
from unittest.mock import patch, MagicMock
from skills import market_portfolio_liquidity_scenario_analyzer

class TestMarketPortfolioLiquidityScenarioAnalyzer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.export_target = f"/tmp/{uuid.uuid4().hex}.json"
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(0.01, 0.20), 4)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(random.randint(2, 5))]
        self.var_val = round(random.uniform(1000.0, 50000.0), 2)
        self.impact = round(random.uniform(500.0, 60000.0), 2)

    def tearDown(self):
        for path in [self.export_target, self.storage_file]:
            if path and not str(path).startswith("s3://") and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_ensure_dir_exists_creates_directory(self):
        nested_dir = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        target_file = f"{nested_dir}/{uuid.uuid4().hex}.json"
        
        market_portfolio_liquidity_scenario_analyzer._ensure_dir_exists(target_file)
        
        self.assertTrue(os.path.exists(nested_dir))
        
        if os.path.exists(target_file):
            os.remove(target_file)
        if os.path.exists(nested_dir):
            os.rmdir(nested_dir)

    def test_ensure_dir_exists_ignores_s3(self):
        s3_path = f"s3://{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        try:
            market_portfolio_liquidity_scenario_analyzer._ensure_dir_exists(s3_path)
        except Exception as e:
            self.fail(f"_ensure_dir_exists failed on S3 path with exception: {e}")

    def test_analyze_liquidity_stress_scenarios_integration(self):
        mock_var_data = {"var": self.var_val, "portfolio_id": self.portfolio_id}
        mock_stress_data = {"impact": self.impact, "symbol": self.symbol}

        with patch("skills.market_portfolio_liquidity_scenario_analyzer._call_calculate_var_and_liquidity", return_value=mock_var_data) as mock_var_call, \
             patch("skills.market_portfolio_liquidity_scenario_analyzer._call_run_stress_scenario_pipeline", return_value=mock_stress_data) as mock_stress_call:

            result = market_portfolio_liquidity_scenario_analyzer.analyze_liquidity_stress_scenarios(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                export_target=self.export_target,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts,
                storage_file=self.storage_file
            )

            mock_var_call.assert_called_once_with(self.portfolio_id, self.confidence_level, self.export_target)
            mock_stress_call.assert_called_once_with(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["var_liquidity_data"], mock_var_data)
            self.assertEqual(result["stress_pipeline_data"], mock_stress_data)
            
            expected_reserve = float(round(max(self.var_val, self.impact) * 1.15, 10))
            self.assertEqual(result["reserve_capital_requirement"], expected_reserve)
            self.assertEqual(result["capital_reserve_requirement"], expected_reserve)

            self.assertTrue(os.path.exists(self.export_target))
            self.assertTrue(os.path.exists(self.storage_file))

            with open(self.export_target, 'r') as f:
                saved_var = json.load(f)
            self.assertEqual(saved_var["var"], self.var_val)

            with open(self.storage_file, 'r') as f:
                saved_stress = json.load(f)
            self.assertEqual(saved_stress["impact"], self.impact)

    def test_market_portfolio_liquidity_scenario_analyzer_class(self):
        mock_var_data = {"var": self.var_val, "portfolio_id": self.portfolio_id}
        mock_stress_data = {"impact": self.impact, "symbol": self.symbol}

        analyzer = market_portfolio_liquidity_scenario_analyzer.MarketPortfolioLiquidityScenarioAnalyzer(storage_file=self.storage_file)

        with patch("skills.market_portfolio_liquidity_scenario_analyzer._call_calculate_var_and_liquidity", return_value=mock_var_data) as mock_var_call, \
             patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_stress_scenario_pipeline") as mock_pipeline_module:

            mock_pipeline_instance = MagicMock()
            mock_pipeline_instance.execute.return_value = mock_stress_data
            mock_pipeline_module.PortfolioStressScenarioPipeline.return_value = mock_pipeline_instance

            result = analyzer.evaluate_portfolio(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                export_target=self.export_target,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_var_call.assert_called_once_with(self.portfolio_id, self.confidence_level, self.export_target)
            mock_pipeline_module.PortfolioStressScenarioPipeline.assert_called_once_with(self.storage_file)
            mock_pipeline_instance.execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["var_result"], mock_var_data)
            self.assertEqual(result["stress_result"], mock_stress_data)

            self.assertTrue(os.path.exists(self.export_target))
            self.assertTrue(os.path.exists(self.storage_file))

    def test_call_calculate_var_and_liquidity_direct(self):
        mock_core = MagicMock()
        mock_core.calculate_var_and_liquidity.return_value = {"var": self.var_val, "portfolio_id": self.portfolio_id}

        with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_var_liquidity_core", mock_core):
            res = market_portfolio_liquidity_scenario_analyzer._call_calculate_var_and_liquidity(
                self.portfolio_id, self.confidence_level, self.export_target
            )
            mock_core.calculate_var_and_liquidity.assert_called_once_with(
                self.portfolio_id, self.confidence_level, self.export_target
            )
            self.assertEqual(res["var"], self.var_val)

    def test_call_run_stress_scenario_pipeline_direct(self):
        mock_pipeline_mod = MagicMock()
        mock_pipeline_mod.run_stress_scenario_pipeline.return_value = {"impact": self.impact}

        with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_stress_scenario_pipeline", mock_pipeline_mod):
            res = market_portfolio_liquidity_scenario_analyzer._call_run_stress_scenario_pipeline(
                self.storage_file, self.symbol, self.percentage, self.shifts
            )
            mock_pipeline_mod.run_stress_scenario_pipeline.assert_called_once_with(
                self.storage_file, self.symbol, self.percentage, self.shifts
            )
            self.assertEqual(res["impact"], self.impact)