import os
import json
import uuid
import random
import unittest
from unittest.mock import patch, MagicMock
import tempfile

from skills import market_portfolio_liquidity_scenario_analyzer
from skills import market_portfolio_var_liquidity_core
from skills import market_portfolio_stress_scenario_pipeline


class TestMarketPortfolioLiquidityScenarioAnalyzer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.symbol = f"SYM{random.randint(100, 999)}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.percentage = round(random.uniform(0.01, 0.20), 4)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        self.var_val = round(random.uniform(1000.0, 50000.0), 2)
        self.impact_val = round(random.uniform(1000.0, 60000.0), 2)

        self.temp_dir = tempfile.TemporaryDirectory()
        self.export_target = os.path.join(self.temp_dir.name, f"export_{uuid.uuid4().hex[:6]}.json")
        self.storage_file = os.path.join(self.temp_dir.name, f"storage_{uuid.uuid4().hex[:6]}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ensure_dir_exists_local(self):
        random_path = os.path.join(self.temp_dir.name, uuid.uuid4().hex, f"{uuid.uuid4().hex}.json")
        market_portfolio_liquidity_scenario_analyzer._ensure_dir_exists(random_path)
        self.assertTrue(os.path.exists(os.path.dirname(random_path)))

    def test_ensure_dir_exists_s3(self):
        s3_path = f"s3://bucket-{uuid.uuid4().hex[:6]}/path/to/object.json"
        try:
            market_portfolio_liquidity_scenario_analyzer._ensure_dir_exists(s3_path)
        except Exception as e:
            self.fail(f"_ensure_dir_exists failed on S3 path: {e}")

    def test_analyze_liquidity_stress_scenarios_integration(self):
        mock_var_data = {"var": self.var_val, "liquidity_score": random.random()}
        mock_stress_data = {"impact": self.impact_val, "details": uuid.uuid4().hex}

        with patch("skills.market_portfolio_var_liquidity_core.calculate_var_and_liquidity", return_value=mock_var_data) as p1, \
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
            self.assertEqual(result["stress_scenario_data"], mock_stress_data)

            expected_reserve = float(round(max(self.var_val, self.impact_val) * 1.15, 10))
            self.assertEqual(result["reserve_capital_requirement"], expected_reserve)
            self.assertEqual(result["capital_reserve_requirement"], expected_reserve)

            self.assertTrue(os.path.exists(self.export_target))
            self.assertTrue(os.path.exists(self.storage_file))

            with open(self.export_target, 'r') as f:
                loaded_var = json.load(f)
            self.assertEqual(loaded_var, mock_var_data)

            with open(self.storage_file, 'r') as f:
                loaded_stress = json.load(f)
            self.assertEqual(loaded_stress, mock_stress_data)

    def test_market_portfolio_liquidity_scenario_analyzer_class(self):
        mock_var_data = {"var": self.var_val, "status": uuid.uuid4().hex}
        mock_stress_data = {"impact": self.impact_val, "status": uuid.uuid4().hex}

        pipeline_mock_instance = MagicMock()
        pipeline_mock_instance.execute.return_value = mock_stress_data

        with patch("skills.market_portfolio_var_liquidity_core.calculate_var_and_liquidity", return_value=mock_var_data) as p1, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline", return_value=pipeline_mock_instance) as p_class:

            analyzer = market_portfolio_liquidity_scenario_analyzer.MarketPortfolioLiquidityScenarioAnalyzer(storage_file=self.storage_file)
            
            reserve = analyzer._calculate_required_reserve(self.var_val, self.impact_val)
            expected_reserve = float(round(max(self.var_val, self.impact_val) * 1.15, 10))
            self.assertEqual(reserve, expected_reserve)

            eval_result = analyzer.evaluate_portfolio(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                export_target=self.export_target,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            p1.assert_called_once_with(self.portfolio_id, self.confidence_level, self.export_target)
            p_class.assert_called_once_with(self.storage_file)
            pipeline_mock_instance.execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)

            self.assertEqual(eval_result["portfolio_id"], self.portfolio_id)
            self.assertEqual(eval_result["var_result"], mock_var_data)
            self.assertEqual(eval_result["stress_result"], mock_stress_data)


if __name__ == "__main__":
    unittest.main()