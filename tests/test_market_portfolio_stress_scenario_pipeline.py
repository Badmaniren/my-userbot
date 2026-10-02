import unittest
from unittest.mock import patch, MagicMock
import json
import io
import uuid
import random
import string
from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline
)

class TestPortfolioStressScenarioPipeline(unittest.TestCase):
    
    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]
        
    def test_pipeline_class_initialization_and_execution_success(self):
        mock_sim_result = {
            "symbol": self.symbol,
            "percentage": self.percentage,
            "simulated_value": round(random.uniform(100.0, 1000.0), 2),
            "var_impact": round(random.uniform(1.0, 10.0), 2)
        }
        mock_stress_result = {
            "symbol": self.symbol,
            "shifts": self.shifts,
            "results": [{"shift": s, "impact": s * 1.5} for s in self.shifts],
            "max_drawdown": round(random.uniform(5.0, 25.0), 2)
        }
        mock_report_result = {
            "symbol": self.symbol,
            "status": "critical",
            "impact_score": int(random.randint(50, 100)),
            "resilience_index": round(random.uniform(0.1, 0.9), 2)
        }
        
        valid_json_data = json.dumps({self.symbol: {"shares": random.randint(10, 100)}})
        
        with patch("builtins.open", create=True) as mock_file:
            mock_file.return_value.__enter__.return_value = io.StringIO(valid_json_data)
            
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
                 patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockReporter:
                
                sim_instance = MockSimulator.return_value
                sim_instance.simulate_scenario.return_value = mock_sim_result
                sim_instance.run_stress_test.return_value = mock_stress_result
                
                rep_instance = MockReporter.return_value
                rep_instance.run_stress_report.return_value = mock_report_result
                
                pipeline = PortfolioStressScenarioPipeline(self.storage_file)
                result = pipeline.execute(self.symbol, self.percentage, self.shifts)
                
                self.assertIsInstance(result, dict)
                self.assertIn("simulation", result)
                self.assertIn("stress_test", result)
                self.assertIn("stress_report", result)
                
                self.assertEqual(result["simulation"]["symbol"], self.symbol)
                self.assertEqual(result["stress_test"]["symbol"], self.symbol)
                self.assertEqual(result["stress_report"]["symbol"], self.symbol)
                
                sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
                sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
                rep_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)

    def test_pipeline_class_execution_with_exceptions_and_fallbacks(self):
        corrupted_data = uuid.uuid4().hex
        
        with patch("builtins.open", create=True) as mock_file:
            mock_file.return_value.__enter__.return_value = io.StringIO(corrupted_data)
            
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
                 patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockReporter:
                
                sim_instance = MockSimulator.return_value
                sim_instance.simulate_scenario.side_effect = KeyError("Missing symbol")
                sim_instance.run_stress_test.side_effect = KeyError("Missing stress data")
                
                rep_instance = MockReporter.return_value
                rep_instance.run_stress_report.side_effect = RuntimeError("Reporter failure")
                
                pipeline = PortfolioStressScenarioPipeline(self.storage_file)
                result = pipeline.execute(self.symbol, self.percentage, self.shifts)
                
                self.assertIsInstance(result, dict)
                self.assertEqual(result["simulation"]["symbol"], self.symbol)
                self.assertEqual(result["simulation"]["simulated_value"], 0.0)
                
                self.assertEqual(result["stress_test"]["symbol"], self.symbol)
                self.assertEqual(result["stress_test"]["results"], [])
                
                self.assertEqual(result["stress_report"]["symbol"], self.symbol)
                self.assertEqual(result["stress_report"]["status"], "default")
                self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_functional_run_stress_scenario_pipeline_success(self):
        mock_sim_list_result = [round(random.uniform(-5.0, 5.0), 2) for _ in range(2)]
        mock_report_result = {
            "symbol": self.symbol,
            "status": "stable",
            "impact_score": int(random.randint(1, 49)),
            "metrics_extended": {"liquidity_drain": round(random.uniform(0.0, 1.0), 2)}
        }
        
        valid_json_data = json.dumps({self.symbol: {"balance": random.randint(1000, 5000)}})
        
        with patch("builtins.open", create=True) as mock_file:
            mock_file.return_value.__enter__.return_value = io.StringIO(valid_json_data)
            
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
                 patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockReporter:
                
                sim_instance = MockSimulator.return_value
                sim_instance.simulate_scenario.return_value = {"value": 42.0}
                sim_instance.run_stress_test.return_value = mock_sim_list_result
                
                rep_instance = MockReporter.return_value
                rep_instance.run_stress_reporting.return_value = mock_report_result
                
                result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)
                
                self.assertIsInstance(result, dict)
                self.assertEqual(result["simulation"]["symbol"], self.symbol)
                self.assertEqual(result["simulation"]["value"], 42.0)
                
                self.assertEqual(result["stress_test"]["symbol"], self.symbol)
                self.assertEqual(result["stress_test"]["shifts"], self.shifts)
                self.assertEqual(result["stress_test"]["results"], mock_sim_list_result)
                
                self.assertEqual(result["stress_report"]["symbol"], self.symbol)
                self.assertEqual(result["stress_report"]["status"], "stable")

    def test_functional_run_stress_scenario_pipeline_file_not_found(self):
        with patch("builtins.open", create=True) as mock_file:
            mock_file.side_effect = [FileNotFoundError, MagicMock()]
            
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
                 patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockReporter:
                
                sim_instance = MockSimulator.return_value
                sim_instance.simulate_scenario.return_value = {"symbol": self.symbol, "simulated_value": 11.1}
                sim_instance.run_stress_test.return_value = {"symbol": self.symbol, "results": []}
                
                rep_instance = MockReporter.return_value
                rep_instance.run_stress_reporting.side_effect = AttributeError("No method")
                
                result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)
                
                self.assertIsInstance(result, dict)
                self.assertEqual(result["stress_report"]["status"], "default")
                self.assertEqual(result["stress_report"]["impact_score"], 0)

if __name__ == "__main__":
    unittest.main()