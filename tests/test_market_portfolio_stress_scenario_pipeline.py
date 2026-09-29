import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import io
import json
from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline
)

class TestPortfolioStressScenarioPipeline(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 3))]

    def test_pipeline_class_execution(self):
        sim_val = round(random.uniform(100.0, 1000.0), 2)
        stress_res = [round(random.uniform(-5.0, 5.0), 2) for _ in range(len(self.shifts))]
        report_res = {"status": f"status_{uuid.uuid4().hex[:4]}", "score": random.randint(1, 100)}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_val
            mock_sim_instance.run_stress_test.return_value = stress_res

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.return_value = report_res

            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            mock_sim_cls.assert_called_once_with(self.storage_file)
            mock_rep_cls.assert_called_once_with(self.storage_file)
            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            mock_rep_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)

            self.assertEqual(result["simulation"], sim_val)
            self.assertEqual(result["stress_test"], stress_res)
            self.assertEqual(result["stress_report"], report_res)

    def test_run_stress_scenario_pipeline_success(self):
        valid_data = {uuid.uuid4().hex: random.randint(1, 100)}
        file_content = json.dumps(valid_data)

        sim_val = {"symbol": self.symbol, "simulated": random.randint(50, 500)}
        stress_list = [round(random.uniform(1.0, 10.0), 2)]
        report_val = {"symbol": self.symbol, "impact": random.randint(1, 10)}

        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_val
            mock_sim_instance.run_stress_test.return_value = stress_list

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = report_val

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"], sim_val)
            self.assertEqual(result["stress_test"]["results"], stress_list)
            self.assertEqual(result["stress_report"], report_val)

    def test_run_stress_scenario_pipeline_file_error_recovery(self):
        malformed_data = uuid.uuid4().hex

        sim_fallback = {"symbol": self.symbol, "percentage": self.percentage, "simulated_value": 0.0}
        stress_fallback = {"symbol": self.symbol, "shifts": self.shifts, "results": []}
        report_fallback = {"symbol": self.symbol, "status": "default", "impact_score": 0}

        with patch("builtins.open", mock_open(read_data=malformed_data)) as mock_file, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError("Sim fail")
            mock_sim_instance.run_stress_test.side_effect = KeyError("Test fail")

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.side_effect = Exception("Report fail")

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"], sim_fallback)
            self.assertEqual(result["stress_test"], stress_fallback)
            self.assertEqual(result["stress_report"], report_fallback)

    def test_run_stress_scenario_pipeline_list_stress_test_formatting(self):
        valid_data = json.dumps({})
        raw_stress_list = [round(random.uniform(-2.0, 2.0), 2), round(random.uniform(-2.0, 2.0), 2)]

        with patch("builtins.open", mock_open(read_data=valid_data)), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {}
            mock_sim_instance.run_stress_test.return_value = raw_stress_list

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = {}

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            expected_stress_dict = {
                "symbol": self.symbol,
                "shifts": self.shifts,
                "results": raw_stress_list
            }
            self.assertEqual(result["stress_test"], expected_stress_dict)

if __name__ == "__main__":
    unittest.main()