import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import io
import uuid
import random
import string
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

    def test_pipeline_class_execution_success(self):
        sim_val = round(random.uniform(100.0, 1000.0), 2)
        test_results = [round(random.uniform(-5.0, 5.0), 2) for _ in range(2)]
        report_score = random.randint(1, 100)

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls, \
             patch("builtins.open", mock_open(read_data=json.dumps({self.symbol: random.randint(1, 10)}))):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {"value": sim_val}
            mock_sim_instance.run_stress_test.return_value = test_results

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.return_value = {"impact_score": report_score}

            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertIsInstance(result, dict)
            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["value"], sim_val)
            self.assertEqual(result["stress_test"]["results"], test_results)
            self.assertEqual(result["stress_report"]["impact_score"], report_score)

    def test_pipeline_class_exception_handling(self):
        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls, \
             patch("builtins.open", side_effect=FileNotFoundError):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError("Missing symbol")
            mock_sim_instance.run_stress_test.side_effect = KeyError("Missing stress data")

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.side_effect = RuntimeError("Failed report")

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

    def test_run_stress_scenario_pipeline_function_success(self):
        sim_val = round(random.uniform(50.0, 500.0), 2)
        test_dict_results = [{"shift": s, "val": s * 2} for s in self.shifts]
        report_status = ''.join(random.choices(string.ascii_lowercase, k=6))

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls, \
             patch("builtins.open", mock_open(read_data=json.dumps({}))):

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {"simulated_value": sim_val}
            mock_sim_instance.run_stress_test.return_value = test_dict_results

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = {"status": report_status}

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["simulated_value"], sim_val)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["results"], test_dict_results)
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], report_status)

    def test_run_stress_scenario_pipeline_invalid_json(self):
        random_garbage = ''.join(random.choices(string.printable, k=15))
        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls, \
             patch("builtins.open", mock_open(read_data=random_garbage)):

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {"symbol": self.symbol, "percentage": self.percentage}
            mock_sim_instance.run_stress_test.return_value = []

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = {"symbol": self.symbol}

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["results"], [])
            self.assertIn("stress_report", result)

    def test_pipeline_stress_test_returns_list_formatting(self):
        list_results = [random.randint(10, 50), random.randint(60, 100)]
        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls, \
             patch("builtins.open", mock_open(read_data="{}")):

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {}
            mock_sim_instance.run_stress_test.return_value = list_results

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = {}

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.shifts)
            self.assertEqual(result["stress_test"]["results"], list_results)

if __name__ == '__main__':
    unittest.main()