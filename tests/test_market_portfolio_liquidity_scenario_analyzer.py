import unittest
from unittest.mock import patch, MagicMock, mock_open
import random
import uuid
import json

from skills import market_portfolio_liquidity_scenario_analyzer
from skills.market_portfolio_liquidity_scenario_analyzer import (
    analyze_liquidity_stress_scenarios,
    MarketPortfolioLiquidityScenarioAnalyzer,
)


class TestMarketPortfolioLiquidityScenarioAnalyzer(unittest.TestCase):

    def _generate_random_string(self, prefix="rnd"):
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    def _generate_random_float(self, low=10.0, high=10000.0):
        return round(random.uniform(low, high), 4)

    def test_analyze_liquidity_stress_scenarios_functions_var_dominant(self):
        portfolio_id = self._generate_random_string("port")
        confidence_level = round(random.uniform(0.90, 0.99), 3)
        symbol = self._generate_random_string("sym").upper()
        percentage = round(random.uniform(0.01, 0.50), 3)
        shifts = {self._generate_random_string("shift"): self._generate_random_float(1.0, 50.0)}

        var_amount = self._generate_random_float(5000.0, 10000.0)
        impact_amount = self._generate_random_float(100.0, 4000.0)

        mock_var_data = {
            self._generate_random_string("meta"): self._generate_random_string("val"),
            "var": var_amount
        }
        mock_stress_data = {
            self._generate_random_string("meta"): self._generate_random_string("val"),
            "impact": impact_amount
        }

        with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_var_liquidity_core") as mock_core:
            with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_stress_scenario_pipeline") as mock_pipeline:
                mock_core.calculate_var_and_liquidity.return_value = mock_var_data
                mock_pipeline.run_stress_scenario_pipeline.return_value = mock_stress_data

                result = analyze_liquidity_stress_scenarios(
                    portfolio_id=portfolio_id,
                    confidence_level=confidence_level,
                    export_target=None,
                    symbol=symbol,
                    percentage=percentage,
                    shifts=shifts,
                    storage_file=None
                )

                mock_core.calculate_var_and_liquidity.assert_called_once_with(portfolio_id, confidence_level, None)
                mock_pipeline.run_stress_scenario_pipeline.assert_called_once_with(None, symbol, percentage, shifts)

                expected_reserve = var_amount * 1.15
                self.assertEqual(result["portfolio_id"], portfolio_id)
                self.assertEqual(result["var_liquidity_data"], mock_var_data)
                self.assertEqual(result["stress_pipeline_data"], mock_stress_data)
                self.assertEqual(result["stress_scenario_data"], mock_stress_data)
                self.assertAlmostEqual(result["reserve_capital_requirement"], expected_reserve, places=4)
                self.assertAlmostEqual(result["capital_reserve_requirement"], expected_reserve, places=4)

    def test_analyze_liquidity_stress_scenarios_class_fallback_impact_dominant(self):
        portfolio_id = self._generate_random_string("port")
        confidence_level = round(random.uniform(0.90, 0.99), 3)
        symbol = self._generate_random_string("sym").upper()
        percentage = round(random.uniform(0.01, 0.50), 3)
        shifts = {self._generate_random_string("key"): self._generate_random_float()}

        var_amount = self._generate_random_float(10.0, 1000.0)
        impact_amount = self._generate_random_float(3000.0, 9000.0)

        mock_var_data = {"var": var_amount, self._generate_random_string("k"): self._generate_random_string("v")}
        mock_stress_data = {"impact": impact_amount, self._generate_random_string("k"): self._generate_random_string("v")}

        with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_var_liquidity_core") as mock_core:
            with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_stress_scenario_pipeline") as mock_pipeline:
                del mock_core.calculate_var_and_liquidity
                del mock_pipeline.run_stress_scenario_pipeline

                mock_core_instance = MagicMock()
                mock_core_instance.calculate_var_and_liquidity.return_value = mock_var_data
                mock_core.market_portfolio_var_liquidity_core.return_value = mock_core_instance

                mock_pipeline_instance = MagicMock()
                mock_pipeline_instance.execute.return_value = mock_stress_data
                mock_pipeline.PortfolioStressScenarioPipeline.return_value = mock_pipeline_instance

                result = analyze_liquidity_stress_scenarios(
                    portfolio_id=portfolio_id,
                    confidence_level=confidence_level,
                    export_target=None,
                    symbol=symbol,
                    percentage=percentage,
                    shifts=shifts,
                    storage_file=None
                )

                mock_core.market_portfolio_var_liquidity_core.assert_called_once()
                mock_core_instance.calculate_var_and_liquidity.assert_called_once_with(portfolio_id, confidence_level, None)
                mock_pipeline.PortfolioStressScenarioPipeline.assert_called_once_with(None)
                mock_pipeline_instance.execute.assert_called_once_with(symbol, percentage, shifts)

                expected_reserve = impact_amount * 1.15
                self.assertEqual(result["portfolio_id"], portfolio_id)
                self.assertAlmostEqual(result["reserve_capital_requirement"], expected_reserve, places=4)

    def test_analyze_liquidity_stress_scenarios_default_missing_var_and_impact(self):
        portfolio_id = self._generate_random_string("port")
        with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_var_liquidity_core") as mock_core:
            with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_stress_scenario_pipeline") as mock_pipeline:
                mock_core.calculate_var_and_liquidity.return_value = {}
                mock_pipeline.run_stress_scenario_pipeline.return_value = {}

                result = analyze_liquidity_stress_scenarios(portfolio_id=portfolio_id)

                self.assertAlmostEqual(result["reserve_capital_requirement"], 0.0, places=4)
                self.assertAlmostEqual(result["capital_reserve_requirement"], 0.0, places=4)

    def test_analyze_liquidity_stress_scenarios_local_file_exports(self):
        portfolio_id = self._generate_random_string("port")
        dir_name = self._generate_random_string("dir")
        export_target = f"/{dir_name}/{self._generate_random_string('export')}.json"
        storage_file = f"/{dir_name}/{self._generate_random_string('storage')}.json"

        mock_var_data = {"var": self._generate_random_float(), "token": self._generate_random_string("var_tok")}
        mock_stress_data = {"impact": self._generate_random_float(), "token": self._generate_random_string("stress_tok")}

        m_open = mock_open()
        with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_var_liquidity_core") as mock_core:
            with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_stress_scenario_pipeline") as mock_pipeline:
                with patch("os.path.exists", return_value=False) as mock_exists:
                    with patch("os.makedirs") as mock_makedirs:
                        with patch("builtins.open", m_open):
                            mock_core.calculate_var_and_liquidity.return_value = mock_var_data
                            mock_pipeline.run_stress_scenario_pipeline.return_value = mock_stress_data

                            result = analyze_liquidity_stress_scenarios(
                                portfolio_id=portfolio_id,
                                export_target=export_target,
                                storage_file=storage_file
                            )

                            self.assertEqual(mock_makedirs.call_count, 2)
                            self.assertEqual(m_open.call_count, 2)
                            m_open.assert_any_call(export_target, 'w')
                            m_open.assert_any_call(storage_file, 'w')
                            self.assertEqual(result["portfolio_id"], portfolio_id)

    def test_analyze_liquidity_stress_scenarios_s3_export_target_bypasses_local_write(self):
        portfolio_id = self._generate_random_string("port")
        s3_bucket = self._generate_random_string("bucket")
        export_target = f"s3://{s3_bucket}/{self._generate_random_string('key')}.json"

        mock_var_data = {"var": self._generate_random_float()}
        mock_stress_data = {"impact": self._generate_random_float()}

        m_open = mock_open()
        with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_var_liquidity_core") as mock_core:
            with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_stress_scenario_pipeline") as mock_pipeline:
                with patch("os.makedirs") as mock_makedirs:
                    with patch("builtins.open", m_open):
                        mock_core.calculate_var_and_liquidity.return_value = mock_var_data
                        mock_pipeline.run_stress_scenario_pipeline.return_value = mock_stress_data

                        analyze_liquidity_stress_scenarios(
                            portfolio_id=portfolio_id,
                            export_target=export_target,
                            storage_file=None
                        )

                        mock_makedirs.assert_not_called()
                        m_open.assert_not_called()

    def test_analyzer_class_calculate_required_reserve(self):
        storage_file = self._generate_random_string("path")
        analyzer = MarketPortfolioLiquidityScenarioAnalyzer(storage_file=storage_file)
        self.assertEqual(analyzer.storage_file, storage_file)

        val_a = self._generate_random_float(100.0, 500.0)
        val_b = self._generate_random_float(600.0, 1000.0)

        reserve_1 = analyzer._calculate_required_reserve(val_a, val_b)
        self.assertAlmostEqual(reserve_1, val_b * 1.15, places=4)

        reserve_2 = analyzer._calculate_required_reserve(val_b, val_a)
        self.assertAlmostEqual(reserve_2, val_b * 1.15, places=4)

    def test_analyzer_evaluate_portfolio_classes_path(self):
        storage_file = self._generate_random_string("store_path")
        analyzer = MarketPortfolioLiquidityScenarioAnalyzer(storage_file=storage_file)

        portfolio_id = self._generate_random_string("port")
        confidence_level = round(random.uniform(0.95, 0.99), 3)
        export_target = self._generate_random_string("exp")
        symbol = self._generate_random_string("sym").upper()
        percentage = round(random.uniform(0.05, 0.25), 3)
        shifts = {self._generate_random_string("sh"): self._generate_random_float()}

        expected_var_res = {self._generate_random_string("k"): self._generate_random_string("v")}
        expected_stress_res = {self._generate_random_string("k"): self._generate_random_string("v")}

        with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_var_liquidity_core") as mock_core:
            with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_stress_scenario_pipeline") as mock_pipeline:
                mock_core_instance = MagicMock()
                mock_core_instance.calculate_var_and_liquidity.return_value = expected_var_res
                mock_core.market_portfolio_var_liquidity_core.return_value = mock_core_instance

                mock_pipe_instance = MagicMock()
                mock_pipe_instance.execute.return_value = expected_stress_res
                mock_pipeline.PortfolioStressScenarioPipeline.return_value = mock_pipe_instance

                result = analyzer.evaluate_portfolio(
                    portfolio_id=portfolio_id,
                    confidence_level=confidence_level,
                    export_target=export_target,
                    symbol=symbol,
                    percentage=percentage,
                    shifts=shifts
                )

                mock_core.market_portfolio_var_liquidity_core.assert_called_once()
                mock_core_instance.calculate_var_and_liquidity.assert_called_once_with(
                    portfolio_id, confidence_level, export_target
                )
                mock_pipeline.PortfolioStressScenarioPipeline.assert_called_once_with(storage_file)
                mock_pipe_instance.execute.assert_called_once_with(symbol, percentage, shifts)

                self.assertEqual(result["portfolio_id"], portfolio_id)
                self.assertEqual(result["var_result"], expected_var_res)
                self.assertEqual(result["stress_result"], expected_stress_res)

    def test_analyzer_evaluate_portfolio_fallback_path(self):
        storage_file = self._generate_random_string("store_fallback")
        analyzer = MarketPortfolioLiquidityScenarioAnalyzer(storage_file=storage_file)

        portfolio_id = self._generate_random_string("port")
        confidence_level = round(random.uniform(0.95, 0.99), 3)
        export_target = self._generate_random_string("target")
        symbol = self._generate_random_string("sym").upper()
        percentage = round(random.uniform(0.05, 0.25), 3)
        shifts = {self._generate_random_string("param"): self._generate_random_float()}

        expected_var_res = {self._generate_random_string("k"): self._generate_random_string("v")}
        expected_stress_res = {self._generate_random_string("k"): self._generate_random_string("v")}

        with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_var_liquidity_core") as mock_core:
            with patch("skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_stress_scenario_pipeline") as mock_pipeline:
                del mock_core.market_portfolio_var_liquidity_core
                del mock_pipeline.PortfolioStressScenarioPipeline

                mock_core.calculate_var_and_liquidity.return_value = expected_var_res
                mock_pipeline.run_stress_scenario_pipeline.return_value = expected_stress_res

                result = analyzer.evaluate_portfolio(
                    portfolio_id=portfolio_id,
                    confidence_level=confidence_level,
                    export_target=export_target,
                    symbol=symbol,
                    percentage=percentage,
                    shifts=shifts
                )

                mock_core.calculate_var_and_liquidity.assert_called_once_with(
                    portfolio_id, confidence_level, export_target
                )
                mock_pipeline.run_stress_scenario_pipeline.assert_called_once_with(
                    storage_file, symbol, percentage, shifts
                )

                self.assertEqual(result["portfolio_id"], portfolio_id)
                self.assertEqual(result["var_result"], expected_var_res)
                self.assertEqual(result["stress_result"], expected_stress_res)


if __name__ == "__main__":
    unittest.main()