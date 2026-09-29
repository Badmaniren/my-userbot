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
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

    def test_pipeline_class_execution(self):
        sim_val = round(random.uniform(100.0, 1000.0), 2)
        stress_res = [{"shift": s, "val": sim_val * 0.9} for s in self.shifts]
        report_res = {"status": "ok", "impact": random.randint(1, 10)}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {"symbol": self.symbol, "simulated": sim_val}
            mock_sim_instance.run_stress_test.return_value = stress_res

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.return_value = report_res

            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"], stress_res)
            self.assertEqual(result["stress_report"], report_res)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            mock_rep_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)

    def test_run_stress_scenario_pipeline_success(self):
        initial_data = {uuid.uuid4().hex: random.randint(1, 100)}
        file_content = json.dumps(initial_data)

        sim_val = round(random.uniform(50.0, 500.0), 2)
        stress_res_list = [round(random.uniform(-5.0, 5.0), 2) for _ in self.shifts]
        report_res = {"symbol": self.symbol, "report_id": uuid.uuid4().hex}

        mock_file = io.StringIO(file_content)

        with patch("builtins.open", return_value=mock_file) as mock_open, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {"val": sim_val}
            mock_sim_instance.run_stress_test.return_value = stress_res_list

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = report_res

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"], {"val": sim_val})
            self.assertEqual(result["stress_test"]["results"], stress_res_list)
            self.assertEqual(result["stress_report"], report_res)

    def test_run_stress_scenario_pipeline_file_error_recovery(self):
        sim_val = 0.0
        report_res = {"symbol": self.symbol, "status": "default", "impact_score": 0}

        with patch("builtins.open", side_effect=[FileNotFoundError, mock_file := io.StringIO("{}"), mock_file := io.StringIO("{}")]) as mock_open, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError("Missing symbol")
            mock_sim_instance.run_stress_test.side_effect = KeyError("Missing shifts")

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.side_effect = Exception("Reporting failed")

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)
            self.assertEqual(result["stress_test"]["results"], [])
            self.assertEqual(result["stress_report"], report_res)

    def test_run_stress_scenario_pipeline_invalid_json_format(self):
        invalid_content = json.dumps([random.randint(1, 10), random.randint(11, 20)])

        with patch("builtins.open", side_effect=[io.StringIO(invalid_content), io.StringIO("{}"), io.StringIO("{}")]) as mock_open, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {"ok": True}
            mock_sim_instance.run_stress_test.return_value = {"data": "test"}

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = {"status": "success"}

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)
            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)

if __name__ == '__main__':
    unittest.main()