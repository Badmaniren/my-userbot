import unittest
from unittest.mock import patch
import io
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 3))]

    def test_pipeline_class_execution_success(self):
        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        
        sim_mock_data = {"symbol": self.symbol, "percentage": self.percentage, "simulated_value": random.uniform(10, 1000)}
        stress_mock_data = [{"shift": s, "impact": random.uniform(-5, 5)} for s in self.shifts]
        report_mock_data = {"symbol": self.symbol, "status": "stable", "impact_score": random.randint(1, 100)}

        with patch.object(pipeline.simulator, 'simulate_scenario', return_value=sim_mock_data) as mock_sim, \
             patch.object(pipeline.simulator, 'run_stress_test', return_value=stress_mock_data) as mock_stress, \
             patch.object(pipeline.reporter, 'run_stress_report', return_value=report_mock_data) as mock_report, \
             patch('builtins.open', side_effect=lambda f, *args, **kwargs: io.StringIO('{}') if 'r' in args[0] or 'r' in kwargs.get('mode', 'r') else io.StringIO()):
            
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)
            
            mock_sim.assert_called_once_with(self.symbol, self.percentage)
            mock_stress.assert_called_once_with(self.symbol, self.shifts)
            mock_report.assert_called_once_with(self.symbol, self.shifts)
            
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["percentage"], self.percentage)
            self.assertEqual(result["stress_test"]["shifts"], self.shifts)

    def test_pipeline_class_execution_exceptions(self):
        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        
        with patch.object(pipeline.simulator, 'simulate_scenario', side_effect=KeyError("Missing key")) as mock_sim, \
             patch.object(pipeline.simulator, 'run_stress_test', side_effect=RuntimeError("Fail")) as mock_stress, \
             patch.object(pipeline.reporter, 'run_stress_report', side_effect=AttributeError("No attr")) as mock_report, \
             patch('builtins.open', side_effect=lambda f, *args, **kwargs: io.StringIO('invalid_json') if 'r' in args[0] or 'r' in kwargs.get('mode', 'r') else io.StringIO()):
            
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)
            
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["percentage"], self.percentage)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)
            
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.shifts)
            self.assertEqual(result["stress_test"]["results"], [])
            
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_functional_pipeline_success(self):
        sim_mock_data = {"symbol": self.symbol, "percentage": self.percentage, "simulated_value": random.uniform(50, 500)}
        stress_mock_data = {"symbol": self.symbol, "shifts": self.shifts, "results": [{"val": random.random()}]}
        report_mock_data = {"symbol": self.symbol, "status": "critical", "impact_score": random.randint(50, 500)}

        with patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_scenario_pipeline.StressReporter') as MockRep, \
             patch('builtins.open', side_effect=lambda f, *args, **kwargs: io.StringIO(json.dumps({})) if 'r' in args[0] or 'r' in kwargs.get('mode', 'r') else io.StringIO()):
            
            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.return_value = sim_mock_data
            instance_sim.run_stress_test.return_value = stress_mock_data

            instance_rep = MockRep.return_value
            instance_rep.run_stress_reporting.return_value = report_mock_data

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], "critical")

    def test_functional_pipeline_exceptions(self):
        with patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_scenario_pipeline.StressReporter') as MockRep, \
             patch('builtins.open', side_effect=FileNotFoundError):
            
            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.side_effect = KeyError("Err")
            instance_sim.run_stress_test.side_effect = RuntimeError("Err")

            instance_rep = MockRep.return_value
            instance_rep.run_stress_reporting.side_effect = AttributeError("Err")

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)
            self.assertEqual(result["stress_test"]["results"], [])
            self.assertEqual(result["stress_report"]["status"], "default")

if __name__ == '__main__':
    unittest.main()