import unittest
from unittest.mock import patch, mock_open
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
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [random.randint(-10, 10), random.randint(-20, 20)]

    def test_load_or_create_storage_success(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        file_content = json.dumps({random_key: random_val})

        with patch("builtins.open", mock_open(read_data=file_content)) as mocked_file:
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            pipeline._load_or_create_storage()
            mocked_file.assert_any_call(self.storage_file, "r", encoding="utf-8", errors="ignore")

    def test_load_or_create_storage_failure_creates_file(self):
        with patch("builtins.open", side_effect=[FileNotFoundError, mock_open().return_code]) as mocked_file:
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            pipeline._load_or_create_storage()
            self.assertTrue(mocked_file.called)

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter")
    def test_pipeline_execute_normal_flow(self, mock_reporter_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_reporter = mock_reporter_cls.return_value

        expected_sim_value = round(random.uniform(100.0, 1000.0), 2)
        mock_simulator.simulate_scenario.return_value = {
            "symbol": self.symbol,
            "percentage": self.percentage,
            "simulated_value": expected_sim_value
        }

        mock_shift_result = random.randint(1, 100)
        mock_simulator.run_stress_test.return_value = [mock_shift_result]

        expected_impact = random.randint(1, 10)
        mock_reporter.run_stress_report.return_value = {
            "symbol": self.symbol,
            "status": "active",
            "impact_score": expected_impact
        }

        with patch("builtins.open", mock_open(read_data="{}")):
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["simulated_value"], expected_sim_value)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["results"], [mock_shift_result])
            self.assertEqual(result["stress_report"]["impact_score"], expected_impact)

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter")
    def test_pipeline_execute_exception_handling(self, mock_reporter_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_reporter = mock_reporter_cls.return_value

        mock_simulator.simulate_scenario.side_effect = RuntimeError("Sim fail")
        mock_simulator.run_stress_test.side_effect = KeyError("Test fail")
        mock_reporter.run_stress_report.side_effect = AttributeError("Report fail")

        with patch("builtins.open", mock_open(read_data="{}")):
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

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter")
    def test_run_stress_scenario_pipeline_standalone(self, mock_stress_reporter_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_reporter = mock_stress_reporter_cls.return_value

        sim_val = round(random.uniform(10.0, 500.0), 2)
        mock_simulator.simulate_scenario.return_value = {"simulated_value": sim_val}
        
        stress_res = [{"shift": s, "val": s * 2} for s in self.shifts]
        mock_simulator.run_stress_test.return_value = stress_res

        report_status = uuid.uuid4().hex
        mock_reporter.run_stress_reporting.return_value = {"status": report_status}

        with patch("builtins.open", mock_open(read_data="{}")):
            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["percentage"], self.percentage)
            self.assertEqual(result["simulation"]["simulated_value"], sim_val)

            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.shifts)
            self.assertEqual(result["stress_test"]["results"], stress_res)

            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], report_status)

if __name__ == "__main__":
    unittest.main()