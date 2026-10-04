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
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.export_target = f"exports/{uuid.uuid4().hex[:8]}.json"
        self.storage_file = f"storage/{uuid.uuid4().hex[:8]}.json"
        self.symbol = f"SYM_{random.choice(['USD', 'EUR', 'BTC', 'ETH'])}"
        self.percentage = round(random.uniform(0.01, 0.20), 4)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]

    def tearDown(self):
        for path in [self.export_target, self.storage_file]:
            if path and not str(path).startswith("s3://"):
                try:
                    if os.path.exists(path):
                        os.remove(path)
                    parent = os.path.dirname(path)
                    if parent and os.path.exists(parent) and not os.listdir(parent):
                        os.rmdir(parent)
                except OSError:
                    pass

    def test_ensure_dir_exists_utility(self):
        random_dir = f"temp_dir_{uuid.uuid4().hex[:8]}"
        random_file = f"{random_dir}/sub_{uuid.uuid4().hex[:8]}.json"
        
        try:
            market_portfolio_liquidity_scenario_analyzer._ensure_dir_exists(random_file)
            self.assertTrue(os.path.exists(random_dir))
        finally:
            if os.path.exists(random_file):
                os.remove(random_file)
            if os.path.exists(random_dir):
                os.rmdir(random_dir)

    def test_analyze_liquidity_stress_scenarios_success(self):
        mock_var_val = round(random.uniform(1000.0, 50000.0), 2)
        mock_impact = round(random.uniform(500.0, 60000.0), 2)
        expected_reserve = float(round(max(mock_var_val, mock_impact) * 1.15, 10))

        var_data = {"var": mock_var_val, "portfolio_id": self.portfolio_id}
        stress_data = {"impact": mock_impact, "symbol": self.symbol}

        with patch("skills.market_portfolio_var_liquidity_core.calculate_var_and_liquidity", return_value=var_data) as mock_calc, \
             patch("skills.market_portfolio_stress_scenario_pipeline.run_stress_scenario_pipeline", return_value=stress_data) as mock_pipeline:

            result = market_portfolio_liquidity_scenario_analyzer.analyze_liquidity_stress_scenarios(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                export_target=self.export_target,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts,
                storage_file=self.storage_file
            )

            mock_calc.assert_called_once_with(self.portfolio_id, self.confidence_level, self.export_target)
            mock_pipeline.assert_called_once_with(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["var_liquidity_data"], var_data)
            self.assertEqual(result["stress_pipeline_data"], stress_data)
            self.assertEqual(result["stress_scenario_data"], stress_data)
            self.assertEqual(result["reserve_capital_requirement"], expected_reserve)
            self.assertEqual(result["capital_reserve_requirement"], expected_reserve)

            self.assertTrue(os.path.exists(self.export_target))
            self.assertTrue(os.path.exists(self.storage_file))

            with open(self.export_target, 'r') as f:
                loaded_export = json.load(f)
            self.assertEqual(loaded_export, var_data)

            with open(self.storage_file, 'r') as f:
                loaded_storage = json.load(f)
            self.assertEqual(loaded_storage, stress_data)

    def test_analyze_liquidity_stress_scenarios_non_dict_outputs(self):
        random_string_var = uuid.uuid4().hex
        random_string_stress = uuid.uuid4().hex
        expected_reserve = float(round(max(0.0, 0.0) * 1.15, 10))

        with patch("skills.market_portfolio_var_liquidity_core.calculate_var_and_liquidity", return_value=random_string_var), \
             patch("skills.market_portfolio_stress_scenario_pipeline.run_stress_scenario_pipeline", return_value=random_string_stress):

            result = market_portfolio_liquidity_scenario_analyzer.analyze_liquidity_stress_scenarios(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                export_target=None,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts,
                storage_file=None
            )

            self.assertEqual(result["var_liquidity_data"], random_string_var)
            self.assertEqual(result["stress_pipeline_data"], random_string_stress)
            self.assertEqual(result["reserve_capital_requirement"], expected_reserve)

    def test_market_portfolio_liquidity_scenario_analyzer_class(self):
        mock_var_result = {"var": random.uniform(100.0, 1000.0), "status": uuid.uuid4().hex}
        mock_stress_result = {"impact": random.uniform(200.0, 2000.0), "status": uuid.uuid4().hex}

        analyzer = market_portfolio_liquidity_scenario_analyzer.MarketPortfolioLiquidityScenarioAnalyzer(storage_file=self.storage_file)

        calculated_reserve = analyzer._calculate_required_reserve(1000.0, 1500.0)
        self.assertEqual(calculated_reserve, float(round(1500.0 * 1.15, 10)))

        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.execute.return_value = mock_stress_result

        with patch("skills.market_portfolio_var_liquidity_core.calculate_var_and_liquidity", return_value=mock_var_result) as mock_calc, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline", return_value=mock_pipeline_instance) as mock_pipeline_class:

            result = analyzer.evaluate_portfolio(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                export_target=self.export_target,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_calc.assert_called_once_with(self.portfolio_id, self.confidence_level, self.export_target)
            mock_pipeline_class.assert_called_once_with(self.storage_file)
            mock_pipeline_instance.execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["var_result"], mock_var_result)
            self.assertEqual(result["stress_result"], mock_stress_result)


if __name__ == "__main__":
    unittest.main()