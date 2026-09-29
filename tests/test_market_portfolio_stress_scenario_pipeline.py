import unittest
from unittest.mock import patch, mock_open
import io
import json
import uuid
import random
import string
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):
    
    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_percentage = round(random.uniform(1.0, 50.0), 2)
        self.random_shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]
        
    def test_pipeline_class_execution(self):
        sim_mock_res = {"symbol": self.random_symbol, "sim": uuid.uuid4().hex}
        stress_mock_res = {"symbol": self.random_symbol, "test": uuid.uuid4().hex}
        report_mock_res = {"symbol": self.random_symbol, "report": uuid.uuid4().hex}
        
        with patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter') as mock_rep_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_mock_res
            mock_sim_instance.run_stress_test.return_value = stress_mock_res
            
            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.return_value = report_mock_res
            
            pipeline = PortfolioStressScenarioPipeline(self.random_storage)
            result = pipeline.execute(self.random_symbol, self.random_percentage, self.random_shifts)
            
            mock_sim_cls.assert_called_once_with(self.random_storage)
            mock_rep_cls.assert_called_once_with(self.random_storage)
            
            mock_sim_instance.simulate_scenario.assert_called_once_with(self.random_symbol, self.random_percentage)
            mock_sim_instance.run_stress_test.assert_called_once_with(self.random_symbol, self.random_shifts)
            mock_rep_instance.run_stress_report.assert_called_once_with(self.random_symbol, self.random_shifts)
            
            self.assertEqual(result["simulation"], sim_mock_res)
            self.assertEqual(result["stress_test"], stress_mock_res)
            self.assertEqual(result["stress_report"], report_mock_res)

    def test_run_stress_scenario_pipeline_valid_json(self):
        valid_data = {uuid.uuid4().hex: random.randint(1, 100)}
        file_content = json.dumps(valid_data)
        
        sim_mock_res = {"symbol": self.random_symbol, "val": uuid.uuid4().hex}
        stress_mock_res = {"symbol": self.random_symbol, "val": uuid.uuid4().hex}
        report_mock_res = {"symbol": self.random_symbol, "val": uuid.uuid4().hex}
        
        with patch('builtins.open', mock_open(read_data=file_content)) as mock_file, \
             patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_scenario_pipeline.StressReporter') as mock_rep_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_mock_res
            mock_sim_instance.run_stress_test.return_value = stress_mock_res
            
            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = report_mock_res
            
            result = run_stress_scenario_pipeline(self.random_storage, self.random_symbol, self.random_percentage, self.random_shifts)
            
            self.assertEqual(result["simulation"], sim_mock_res)
            self.assertEqual(result["stress_test"], stress_mock_res)
            self.assertEqual(result["stress_report"], report_mock_res)
            
            mock_file.assert_any_call(self.random_storage, "r")

    def test_run_stress_scenario_pipeline_invalid_json_fallback(self):
        corrupted_content = uuid.uuid4().hex
        
        with patch('builtins.open', mock_open(read_data=corrupted_content)) as mock_file, \
             patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_scenario_pipeline.StressReporter') as mock_rep_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError
            mock_sim_instance.run_stress_test.side_effect = KeyError
            
            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.side_effect = Exception
            
            result = run_stress_scenario_pipeline(self.random_storage, self.random_symbol, self.random_percentage, self.random_shifts)
            
            self.assertEqual(result["simulation"]["symbol"], self.random_symbol)
            self.assertEqual(result["simulation"]["percentage"], self.random_percentage)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)
            
            self.assertEqual(result["stress_test"]["symbol"], self.random_symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.random_shifts)
            self.assertEqual(result["stress_test"]["results"], [])
            
            self.assertEqual(result["stress_report"]["symbol"], self.random_symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)
            
            mock_file.assert_any_call(self.random_storage, "w")

if __name__ == '__main__':
    unittest.main()