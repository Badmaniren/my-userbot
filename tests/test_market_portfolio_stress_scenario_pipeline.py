import unittest
from unittest.mock import patch, MagicMock
import io
import json
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
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(2, 5))]

    def test_load_or_create_storage_success(self):
        random_dict_data = {uuid.uuid4().hex: random.randint(1, 100)}
        mock_file_content = json.dumps(random_dict_data)
        
        with patch("builtins.open", unittest.mock.mock_open(read_data=mock_file_content)) as mock_file:
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            pipeline._load_or_create_storage()
            mock_file.assert_any_call(self.storage_file, "r", encoding="utf-8", errors="ignore")

    def test_load_or_create_storage_invalid_data(self):
        invalid_content = json.dumps([random.randint(1, 50), random.randint(51, 100)])
        
        with patch("builtins.open", unittest.mock.mock_open(read_data=invalid_content)) as mock_file:
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            pipeline._load_or_create_storage()
            mock_file.assert_any_call(self.storage_file, "w", encoding="utf-8")

    def test_pipeline_execute_nominal_flow(self):
        sim_val = round(random.uniform(100.0, 1000.0), 2)
        mock_sim_result = {"symbol": self.symbol, "percentage": self.percentage, "simulated_value": sim_val}
        
        mock_stress_results = [{"shift": s, "result": random.randint(-50, 50)} for s in self.shifts]
        mock_report_result = {"symbol": self.symbol, "status": "active", "impact_score": random.randint(1, 10)}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockReporter, \
             patch("builtins.open", unittest.mock.mock_open(read_data="{}")):
            
            instance_sim = MockSimulator.return_value
            instance_sim.simulate_scenario.return_value = mock_sim_result
            instance_sim.run_stress_test.return_value = mock_stress_results

            instance_rep = MockReporter.return_value
            instance_rep.run_stress_report.return_value = mock_report_result

            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertIsInstance(result, dict)
            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)
            
            self.assertEqual(result["simulation"]["simulated_value"], sim_val)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["impact_score"], mock_report_result["impact_score"])

    def test_pipeline_execute_exception_handling(self):
        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockReporter, \
             patch("builtins.open", unittest.mock.mock_open(read_data="{}")):
            
            instance_sim = MockSimulator.return_value
            instance_sim.simulate_scenario.side_effect = KeyError("Missing key")
            instance_sim.run_stress_test.side_effect = RuntimeError("Engine failure")

            instance_rep = MockReporter.return_value
            instance_rep.run_stress_report.side_effect = AttributeError("No attribute")

            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
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

    def test_run_stress_scenario_pipeline_function(self):
        sim_val = round(random.uniform(500.0, 5000.0), 2)
        mock_sim_result = {"symbol": self.symbol, "simulated_value": sim_val}
        mock_stress_list = [random.randint(1, 10)]
        mock_report_result = {"status": "ok", "impact_score": random.randint(10, 20)}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockReporter, \
             patch("builtins.open", unittest.mock.mock_open(read_data="{}")):

            instance_sim = MockSimulator.return_value
            instance_sim.simulate_scenario.return_value = mock_sim_result
            instance_sim.run_stress_test.return_value = mock_stress_list

            instance_rep = MockReporter.return_value
            instance_rep.run_stress_reporting.return_value = mock_report_result

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["percentage"], self.percentage)
            self.assertEqual(result["stress_test"]["results"], mock_stress_list)
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["impact_score"], mock_report_result["impact_score"])

if __name__ == "__main__":
    unittest.main()