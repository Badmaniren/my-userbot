import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

    def test_load_or_create_storage_valid_file(self):
        random_content = json.dumps({uuid.uuid4().hex: random.randint(1, 100)})
        with patch("builtins.open", unittest.mock.mock_open(read_data=random_content)) as mock_file:
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            pipeline._load_or_create_storage()
            mock_file.assert_any_call(self.storage_file, "r", encoding="utf-8", errors="ignore")

    def test_load_or_create_storage_invalid_file(self):
        with patch("builtins.open", unittest.mock.mock_open(read_data="invalid_json")) as mock_file:
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            pipeline._load_or_create_storage()
            mock_file.assert_called_with(self.storage_file, "w", encoding="utf-8")

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter")
    def test_pipeline_execute_success(self, mock_reporter_cls, mock_simulator_cls):
        sim_instance = mock_simulator_cls.return_value
        rep_instance = mock_reporter_cls.return_value

        sim_value = round(random.uniform(100.0, 1000.0), 2)
        sim_instance.simulate_scenario.return_value = {"simulated_value": sim_value}
        
        stress_results = [{"shift": s, "val": random.randint(1, 50)} for s in self.shifts]
        sim_instance.run_stress_test.return_value = stress_results

        report_status = uuid.uuid4().hex
        rep_instance.run_stress_report.return_value = {"status": report_status}

        with patch("builtins.open", unittest.mock.mock_open(read_data="{}")):
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["percentage"], self.percentage)
            self.assertEqual(result["simulation"]["simulated_value"], sim_value)

            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.shifts)
            self.assertEqual(result["stress_test"]["results"], stress_results)

            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], report_status)

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter")
    def test_pipeline_execute_key_errors(self, mock_reporter_cls, mock_simulator_cls):
        sim_instance = mock_simulator_cls.return_value
        rep_instance = mock_reporter_cls.return_value

        sim_instance.simulate_scenario.side_effect = KeyError("sim_error")
        sim_instance.run_stress_test.side_effect = KeyError("stress_error")
        rep_instance.run_stress_report.side_effect = KeyError("report_error")

        with patch("builtins.open", unittest.mock.mock_open(read_data="{}")):
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["percentage"], self.percentage)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)

            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["results"], [])

            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], "default")

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter")
    def test_run_stress_scenario_pipeline_functional(self, mock_stress_reporter_cls, mock_simulator_cls):
        sim_instance = mock_simulator_cls.return_value
        rep_instance = mock_stress_reporter_cls.return_value

        sim_value = round(random.uniform(50.0, 500.0), 2)
        sim_instance.simulate_scenario.return_value = {"simulated_value": sim_value}
        
        sim_instance.run_stress_test.return_value = self.shifts

        impact = random.randint(10, 100)
        rep_instance.run_stress_reporting.return_value = {"impact_score": impact}

        with patch("builtins.open", unittest.mock.mock_open(read_data="{}")):
            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["simulated_value"], sim_value)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["results"], self.shifts)
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["impact_score"], impact)

    @patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter")
    def test_run_stress_scenario_pipeline_exceptions(self, mock_stress_reporter_cls, mock_simulator_cls):
        sim_instance = mock_simulator_cls.return_value
        rep_instance = mock_stress_reporter_cls.return_value

        sim_instance.simulate_scenario.side_effect = RuntimeError("sim_fail")
        sim_instance.run_stress_test.side_effect = RuntimeError("stress_fail")
        rep_instance.run_stress_reporting.side_effect = AttributeError("report_fail")

        with patch("builtins.open", unittest.mock.mock_open(read_data="invalid")):
            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["results"], [])
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

if __name__ == '__main__':
    unittest.main()