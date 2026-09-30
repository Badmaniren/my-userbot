import unittest
import json
import uuid
import random
import io
from unittest.mock import patch, MagicMock
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:5].upper()}"
        self.percentage = random.uniform(0.01, 0.5)
        self.shifts = [random.randint(-100, 100) for _ in range(3)]

    def test_pipeline_execution_success(self):
        with patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter') as MockRep:
            
            instance_sim = MockSim.return_value
            instance_rep = MockRep.return_value
            
            expected_sim = {"val": random.random()}
            expected_stress = {"data": [random.randint(1, 10)]}
            expected_report = {"score": random.randint(1, 100)}
            
            instance_sim.simulate_scenario.return_value = expected_sim
            instance_sim.run_stress_test.return_value = expected_stress
            instance_rep.run_stress_report.return_value = expected_report
            
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)
            
            self.assertEqual(result["simulation"], expected_sim)
            self.assertEqual(result["stress_test"], expected_stress)
            self.assertEqual(result["stress_report"], expected_report)
            instance_sim.simulate_scenario.assert_called_with(self.symbol, self.percentage)

    def test_run_stress_scenario_pipeline_file_recovery(self):
        bad_file = f"{uuid.uuid4().hex}.json"
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = FileNotFoundError
            
            result = run_stress_scenario_pipeline(bad_file, self.symbol, self.percentage, self.shifts)
            
            self.assertIn("simulation", result)
            self.assertIsInstance(result["simulation"], dict)
            mock_open.assert_any_call(bad_file, "w", encoding="utf-8")

    def test_run_stress_scenario_pipeline_error_handling(self):
        with patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_scenario_pipeline.StressReporter') as MockRep, \
             patch('builtins.open') as mock_open:
            
            mock_open.return_value.__enter__.return_value = io.StringIO('{}')
            
            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.side_effect = KeyError
            instance_sim.run_stress_test.side_effect = KeyError
            
            instance_rep = MockRep.return_value
            instance_rep.run_stress_reporting.side_effect = RuntimeError
            
            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)
            
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)
            self.assertEqual(result["stress_test"]["results"], [])
            self.assertEqual(result["stress_report"]["impact_score"], 0)
            self.assertEqual(result["stress_report"]["status"], "default")

    def test_run_stress_scenario_pipeline_data_integrity(self):
        random_val = random.uniform(10, 1000)
        with patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator') as MockSim, \
             patch('builtins.open') as mock_open:
            
            mock_open.return_value.__enter__.return_value = io.StringIO(json.dumps({"key": "val"}))
            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.return_value = {"val": random_val}
            instance_sim.run_stress_test.return_value = [1, 2, 3]
            
            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)
            
            self.assertEqual(result["simulation"]["val"], random_val)
            self.assertEqual(result["stress_test"]["results"], [1, 2, 3])
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)

if __name__ == '__main__':
    unittest.main()