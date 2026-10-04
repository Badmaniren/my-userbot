import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io
from skills import market_portfolio_liquidity_scenario_analyzer

class TestMarketPortfolioLiquidityScenarioAnalyzer(unittest.TestCase):
    def test_ensure_dir_exists(self):
        rand_dir = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        rand_file = f"{rand_dir}/{uuid.uuid4().hex}.json"
        
        market_portfolio_liquidity_scenario_analyzer._ensure_dir_exists(rand_file)
        self.assertTrue(os.path.exists(rand_dir))
        
        if os.path.exists(rand_dir):
            os.rmdir(rand_dir)

    def test_analyze_liquidity_stress_scenarios_logic(self):
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.9, 0.99), 2)
        export_target = f"/tmp/{uuid.uuid4().hex}.json"
        storage_file = f"/tmp/{uuid.uuid4().hex}.json"
        symbol = uuid.uuid4().hex[:5].upper()
        percentage = round(random.uniform(5.0, 25.0), 2)
        shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]

        mock_var_data = {"var": random.uniform(1000.0, 5000.0)}
        mock_stress_data = {"impact": random.uniform(2000.0, 6000.0)}

        with patch("skills.market_portfolio_var_liquidity_core.calculate_var_and_liquidity", return_value=mock_var_data), \
             patch("skills.market_portfolio_stress_scenario_pipeline.run_stress_scenario_pipeline", return_value=mock_stress_data):
            
            result = market_portfolio_liquidity_scenario_analyzer.analyze_liquidity_stress_scenarios(
                portfolio_id=portfolio_id,
                confidence_level=confidence_level,
                export_target=export_target,
                symbol=symbol,
                percentage=percentage,
                shifts=shifts,
                storage_file=storage_file
            )

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["var_liquidity_data"], mock_var_data)
            self.assertEqual(result["stress_pipeline_data"], mock_stress_data)
            
            expected_reserve = max(mock_var_data["var"], mock_stress_data["impact"]) * 1.15
            self.assertAlmostEqual(result["reserve_capital_requirement"], expected_reserve)

        for f_path in [export_target, storage_file]:
            if os.path.exists(f_path):
                os.remove(f_path)

    def test_market_portfolio_liquidity_scenario_analyzer_class(self):
        storage_file = f"/tmp/{uuid.uuid4().hex}.json"
        portfolio_id = uuid.uuid4().hex
        confidence_level = round(random.uniform(0.9, 0.99), 2)
        export_target = f"/tmp/{uuid.uuid4().hex}.json"
        symbol = uuid.uuid4().hex[:5].upper()
        percentage = round(random.uniform(1.0, 10.0), 2)
        shifts = [round(random.uniform(-0.05, 0.05), 4) for _ in range(2)]

        mock_var_res = {"liquidity_score": random.uniform(50.0, 100.0)}
        mock_stress_res = {"scenario_result": uuid.uuid4().hex}

        analyzer = market_portfolio_liquidity_scenario_analyzer.MarketPortfolioLiquidityScenarioAnalyzer(storage_file=storage_file)

        with patch("skills.market_portfolio_var_liquidity_core.calculate_var_and_liquidity", return_value=mock_var_res), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline") as mock_pipeline_class:
            
            mock_instance = mock_pipeline_class.return_value
            mock_instance.execute.return_value = mock_stress_res

            res = analyzer.evaluate_portfolio(
                portfolio_id=portfolio_id,
                confidence_level=confidence_level,
                export_target=export_target,
                symbol=symbol,
                percentage=percentage,
                shifts=shifts
            )

            self.assertEqual(res["portfolio_id"], portfolio_id)
            self.assertEqual(res["var_result"], mock_var_res)
            self.assertEqual(res["stress_result"], mock_stress_res)

        if os.path.exists(storage_file):
            os.remove(storage_file)
        if os.path.exists(export_target):
            os.remove(export_target)

if __name__ == "__main__":
    unittest.main()