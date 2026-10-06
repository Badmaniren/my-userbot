import unittest
from unittest.mock import patch, MagicMock
import json
import io
import uuid
import random
import string
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):
    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_percentage = round(random.uniform(-50.0, 50.0), 2)
        self.random_shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

    def test_load_or_create_storage_success(self):
        pipeline = PortfolioStressScenarioPipeline(self.random_storage)
        mock_file_data = json.dumps({uuid.uuid4().hex: random.randint(1, 100)})
        mock_file = io.StringIO(mock_file_data)
        
        with patch("builtins.open", return_value=mock_file) as mock_open:
            pipeline._load_or_create_storage()
            mock_open.assert_called()

    def test_load_or_create_storage_file_not_found(self):
        pipeline = PortfolioStressScenarioPipeline(self.random_storage)
        mock_file = io.StringIO("{}")
        
        with patch("builtins.open", side_effect=[FileNotFoundError, mock_file]) as mock_open:
            pipeline._load_or_create_storage()
            self.assertEqual(mock_open.call_count, 2)

    def test_execute_pipeline_full_flow(self):
        pipeline = PortfolioStressScenarioPipeline(self.random_storage)
        
        sim_mock_result = {"symbol": self.random_symbol, "percentage": self.random_percentage, "simulated_value": random.uniform(100, 1000)}
        stress_mock_result = [{"shift": s, "impact": random.uniform(-5, 5)} for s in self.random_shifts]
        report_mock_result = {"symbol": self.random_symbol, "status": "stable", "impact_score": random.randint(1, 10)}

        with patch.object(pipeline.simulator, "simulate_scenario", return_value=sim_mock_result) as mock_sim, \
             patch.object(pipeline.simulator, "run_stress_test", return_value=stress_mock_result) as mock_stress, \
             patch.object(pipeline.reporter, "run_stress_report", return_value=report_mock_result) as mock_rep, \
             patch("builtins.open", return_value=io.StringIO("{}")):
            
            result = pipeline.execute(self.random_symbol, self.random_percentage, self.random_shifts)
            
            mock_sim.assert_called_once_with(self.random_symbol, self.random_percentage)
            mock_stress.assert_called_once_with(self.random_symbol, self.random_shifts)
            mock_rep.assert_called_once_with(self.random_symbol, self.random_shifts)

            self.assertEqual(result["simulation"]["symbol"], self.random_symbol)
            self.assertEqual(result["simulation"]["percentage"], self.random_percentage)
            self.assertEqual(result["stress_test"]["symbol"], self.random_symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.random_shifts)
            self.assertEqual(result["stress_report"]["symbol"], self.random_symbol)

    def test_execute_pipeline_exceptions_handling(self):
        pipeline = PortfolioStressScenarioPipeline(self.random_storage)

        with patch.object(pipeline.simulator, "simulate_scenario", side_effect=KeyError("Missing key")) as mock_sim, \
             patch.object(pipeline.simulator, "run_stress_test", side_effect=RuntimeError("Error")) as mock_stress, \
             patch.object(pipeline.reporter, "run_stress_report", side_effect=AttributeError("Attr error")) as mock_rep, \
             patch("builtins.open", return_value=io.StringIO("{}")):
            
            result = pipeline.execute(self.random_symbol, self.random_percentage, self.random_shifts)

            self.assertEqual(result["simulation"]["symbol"], self.random_symbol)
            self.assertEqual(result["simulation"]["percentage"], self.random_percentage)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)

            self.assertEqual(result["stress_test"]["symbol"], self.random_symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.random_shifts)
            self.assertEqual(result["stress_test"]["results"], [])

            self.assertEqual(result["stress_report"]["symbol"], self.random_symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_run_stress_scenario_pipeline_functional(self):
        sim_mock_result = {"symbol": self.random_symbol, "percentage": self.random_percentage, "simulated_value": random.uniform(50, 500)}
        stress_mock_result = {"symbol": self.random_symbol, "shifts": self.random_shifts, "results": [1, 2, 3]}
        report_mock_result = {"symbol": self.random_symbol, "status": "alert", "impact_score": 99}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockReporter, \
             patch("builtins.open", return_value=io.StringIO("{}")):
            
            instance_sim = MockSimulator.return_value
            instance_sim.simulate_scenario.return_value = sim_mock_result
            instance_sim.run_stress_test.return_value = stress_mock_result

            instance_rep = MockReporter.return_value
            instance_rep.run_stress_reporting.return_value = report_mock_result

            result = run_stress_scenario_pipeline(self.random_storage, self.random_symbol, self.random_percentage, self.random_shifts)

            self.assertEqual(result["simulation"], sim_mock_result)
            self.assertEqual(result["stress_test"], stress_mock_result)
            self.assertEqual(result["stress_report"], report_mock_result)

    def test_run_stress_scenario_pipeline_exceptions(self):
        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockReporter, \
             patch("builtins.open", return_value=io.StringIO("{}")):
            
            instance_sim = MockSimulator.return_value
            instance_sim.simulate_scenario.side_effect = KeyError("Sim error")
            instance_sim.run_stress_test.side_effect = RuntimeError("Test error")

            instance_rep = MockReporter.return_value
            instance_rep.run_stress_reporting.side_effect = AttributeError("Report error")

            result = run_stress_scenario_pipeline(self.random_storage, self.random_symbol, self.random_percentage, self.random_shifts)

            self.assertEqual(result["simulation"]["symbol"], self.random_symbol)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)

            self.assertEqual(result["stress_test"]["symbol"], self.random_symbol)
            self.assertEqual(result["stress_test"]["results"], [])

            self.assertEqual(result["stress_report"]["symbol"], self.random_symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

if __name__ == "__main__":
    unittest.main()