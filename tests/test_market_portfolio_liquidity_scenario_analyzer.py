import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import io

from skills import market_portfolio_liquidity_scenario_analyzer
from skills import market_portfolio_var_liquidity_core
from skills import market_portfolio_stress_scenario_pipeline


class TestMarketPortfolioLiquidityScenarioAnalyzer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(0.01, 0.25), 4)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(random.randint(2, 5))]
        
        self.export_target = os.path.join(uuid.uuid4().hex, f"{uuid.uuid4().hex}.json")
        self.storage_file = os.path.join(uuid.uuid4().hex, f"{uuid.uuid4().hex}.json")

    def tearDown(files_self):
        for path in [files_self.export_target, files_self.storage_file]:
            if path and not path.startswith("s3://"):
                try:
                    if os.path.exists(path):
                        os.remove(path)
                    dir_path = os.path.dirname(path)
                    if dir_path and os.path.exists(dir_path):
                        os.rmdir(dir_path)
                except Exception:
                    pass

    def test_ensure_dir_exists_local(self):
        rand_dir = uuid.uuid4().hex
        rand_file = f"{uuid.uuid4().hex}.json"
        target_path = os.path.join(rand_dir, rand_file)
        
        try:
            market_portfolio_liquidity_scenario_analyzer._ensure_dir_exists(target_path)
            self.assertTrue(os.path.exists(rand_dir))
        finally:
            if os.path.exists(target_path):
                os.remove(target_path)
            if os.path.exists(rand_dir):
                os.rmdir(rand_dir)

    def test_ensure_dir_exists_s3(self):
        s3_path = f"s3://{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        try:
            market_portfolio_liquidity_scenario_analyzer._ensure_dir_exists(s3_path)
        except Exception as e:
            self.fail(f"_ensure_dir_exists failed for s3 path with error: {e}")

    def test_call_calculate_var_and_liquidity_with_function(self):
        expected_var = round(random.uniform(100.0, 5000.0), 2)
        mock_return = {"var": expected_var, "portfolio_id": self.portfolio_id}
        
        with patch.object(market_portfolio_var_liquidity_core, "calculate_var_and_liquidity", create=True) as mock_func:
            mock_func.return_value = mock_return
            
            if hasattr(market_portfolio_var_liquidity_core, "MarketPortfolioVarLiquidityCore"):
                delattr(market_portfolio_var_liquidity_core, "MarketPortfolioVarLiquidityCore")

            res = market_portfolio_liquidity_scenario_analyzer._call_calculate_var_and_liquidity(
                self.portfolio_id, self.confidence_level, self.export_target
            )
            
            self.assertEqual(res["var"], expected_var)
            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            mock_func.assert_called_once_with(self.portfolio_id, self.confidence_level, self.export_target)

    def test_call_run_stress_scenario_pipeline_with_function(self):
        expected_impact = round(random.uniform(50.0, 2000.0), 2)
        mock_return = {"impact": expected_impact}

        with patch.object(market_portfolio_stress_scenario_pipeline, "run_stress_scenario_pipeline", create=True) as mock_func:
            mock_func.return_value = mock_return
            
            if hasattr(market_portfolio_stress_scenario_pipeline, "PortfolioStressScenarioPipeline"):
                delattr(market_portfolio_stress_scenario_pipeline, "PortfolioStressScenarioPipeline")

            res = market_portfolio_liquidity_scenario_analyzer._call_run_stress_scenario_pipeline(
                self.storage_file, self.symbol, self.percentage, self.shifts
            )

            self.assertEqual(res["impact"], expected_impact)
            mock_func.assert_called_once_with(self.storage_file, self.symbol, self.percentage, self.shifts)

    def test_analyze_liquidity_stress_scenarios_integration(self):
        var_val = round(random.uniform(500.0, 1500.0), 2)
        impact_val = round(random.uniform(600.0, 1800.0), 2)
        
        mock_var_data = {"var": var_val, "portfolio_id": self.portfolio_id}
        mock_stress_data = {"impact": impact_val, "symbol": self.symbol}

        with patch("skills.market_portfolio_liquidity_scenario_analyzer._call_calculate_var_and_liquidity") as mock_var_call, \
             patch("skills.market_portfolio_liquidity_scenario_analyzer._call_run_stress_scenario_pipeline") as mock_stress_call:
            
            mock_var_call.return_value = mock_var_data
            mock_stress_call.return_value = mock_stress_data

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
            self.assertEqual(result["var_liquidity_data"], mock_var_data)
            self.assertEqual(result["stress_pipeline_data"], mock_stress_data)
            self.assertEqual(result["stress_scenario_data"], mock_stress_data)
            
            expected_reserve = float(round(max(var_val, impact_val) * 1.15, 10))
            self.assertEqual(result["reserve_capital_requirement"], expected_reserve)
            self.assertEqual(result["capital_reserve_requirement"], expected_reserve)

            self.assertTrue(os.path.exists(self.export_target))
            self.assertTrue(os.path.exists(self.storage_file))

            with open(self.export_target, 'r') as f:
                loaded_var = json.load(f)
            self.assertEqual(loaded_var["var"], var_val)

            with open(self.storage_file, 'r') as f:
                loaded_stress = json.load(f)
            self.assertEqual(loaded_stress["impact"], impact_val)

    def test_market_portfolio_liquidity_scenario_analyzer_class(self):
        var_val = round(random.uniform(100.0, 900.0), 2)
        impact_val = round(random.uniform(200.0, 1200.0), 2)

        mock_var_data = {"var": var_val}
        mock_stress_data = {"impact": impact_val}

        analyzer = market_portfolio_liquidity_scenario_analyzer.MarketPortfolioLiquidityScenarioAnalyzer(
            storage_file=self.storage_file
        )

        self.assertEqual(analyzer.storage_file, self.storage_file)
        
        expected_reserve = analyzer._calculate_required_reserve(var_val, impact_val)
        self.assertEqual(expected_reserve, float(round(max(var_val, impact_val) * 1.15, 10)))

        with patch("skills.market_portfolio_liquidity_scenario_analyzer._call_calculate_var_and_liquidity") as mock_var_call, \
             patch.object(market_portfolio_stress_scenario_pipeline, "run_stress_scenario_pipeline", create=True) as mock_stress_func:
            
            mock_var_call.return_value = mock_var_data
            mock_stress_func.return_value = mock_stress_data

            if hasattr(market_portfolio_stress_scenario_pipeline, "PortfolioStressScenarioPipeline"):
                delattr(market_portfolio_stress_scenario_pipeline, "PortfolioStressScenarioPipeline")

            res = analyzer.evaluate_portfolio(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                export_target=self.export_target,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["var_result"], mock_var_data)
            self.assertEqual(res["stress_result"], mock_stress_data)

            self.assertTrue(os.path.exists(self.export_target))
            self.assertTrue(os.path.exists(self.storage_file))