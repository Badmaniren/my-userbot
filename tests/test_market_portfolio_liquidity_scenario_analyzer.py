import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io
import string

from skills.market_portfolio_liquidity_scenario_analyzer import (
    analyze_liquidity_stress_scenarios,
    MarketPortfolioLiquidityScenarioAnalyzer
)

class TestMarketPortfolioLiquidityScenarioAnalyzer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.export_target = f"s3://bucket-{uuid.uuid4().hex[:6]}/report.csv"
        self.symbol = f"SYM_{''.join(random.choices(string.ascii_uppercase, k=3))}"
        self.percentage = round(random.uniform(0.05, 0.50), 2)
        self.shifts = {f"factor_{uuid.uuid4().hex[:4]}": round(random.uniform(-0.1, 0.1), 4) for _ in range(3)}
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.db"

    @patch('skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_var_liquidity_core')
    @patch('skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_stress_scenario_pipeline')
    def test_analyze_liquidity_stress_scenarios_success(self, mock_stress_pipeline, mock_var_core):
        expected_var = round(random.uniform(10000.0, 500000.0), 2)
        expected_liquidity_score = round(random.uniform(0.1, 1.0), 4)
        mock_var_core.calculate_var_and_liquidity.return_value = {
            "var": expected_var,
            "liquidity_score": expected_liquidity_score,
            "target": self.export_target
        }

        expected_pipeline_result = {
            "symbol": self.symbol,
            "status": "SHOCKED",
            "impact": round(random.uniform(1000.0, 50000.0), 2)
        }
        mock_stress_pipeline.run_stress_scenario_pipeline.return_value = expected_pipeline_result

        result = analyze_liquidity_stress_scenarios(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_target,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts,
            storage_file=self.storage_file
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["var_liquidity_data"]["var"], expected_var)
        self.assertEqual(result["stress_pipeline_data"]["symbol"], self.symbol)
        self.assertIn("reserve_capital_requirement", result)

        mock_var_core.calculate_var_and_liquidity.assert_called_once_with(
            self.portfolio_id, self.confidence_level, self.export_target
        )
        mock_stress_pipeline.run_stress_scenario_pipeline.assert_called_once_with(
            self.storage_file, self.symbol, self.percentage, self.shifts
        )

    @patch('skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_var_liquidity_core')
    @patch('skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_stress_scenario_pipeline')
    def test_analyzer_class_execution(self, mock_stress_pipeline, mock_var_core):
        core_instance = MagicMock()
        mock_var_core.market_portfolio_var_liquidity_core.return_value = core_instance
        
        expected_var = round(random.uniform(5000.0, 100000.0), 2)
        core_instance.calculate_var_and_liquidity.return_value = {"var": expected_var}

        pipeline_instance = MagicMock()
        mock_stress_pipeline.PortfolioStressScenarioPipeline.return_value = pipeline_instance
        pipeline_instance.execute.return_value = {"status": "SUCCESS", "shift_applied": True}

        analyzer = MarketPortfolioLiquidityScenarioAnalyzer(storage_file=self.storage_file)
        analysis_result = analyzer.evaluate_portfolio(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_target,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(analysis_result, dict)
        self.assertEqual(analysis_result["var_result"]["var"], expected_var)
        self.assertEqual(analysis_result["stress_result"]["status"], "SUCCESS")

        mock_stress_pipeline.PortfolioStressScenarioPipeline.assert_called_once_with(self.storage_file)
        pipeline_instance.execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)

    @patch('skills.market_portfolio_liquidity_scenario_analyzer.market_portfolio_var_liquidity_core')
    def test_liquidity_core_exception_handling(self, mock_var_core):
        error_message = f"err_{uuid.uuid4().hex}"
        mock_var_core.calculate_var_and_liquidity.side_effect = RuntimeError(error_message)

        with self.assertRaises(RuntimeError) as ctx:
            analyze_liquidity_stress_scenarios(
                portfolio_id=self.portfolio_id,
                confidence_level=self.confidence_level,
                export_target=self.export_target,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts,
                storage_file=self.storage_file
            )
        self.assertIn(error_message, str(ctx.exception))

    def test_reserve_capital_calculation_logic(self):
        analyzer = MarketPortfolioLiquidityScenarioAnalyzer(storage_file=self.storage_file)
        var_val = round(random.uniform(10000.0, 50000.0), 2)
        stress_impact = round(random.uniform(5000.0, 25000.0), 2)
        
        reserve = analyzer._calculate_required_reserve(var_val, stress_impact)
        self.assertGreaterEqual(reserve, max(var_val, stress_impact))

if __name__ == '__main__':
    unittest.main()