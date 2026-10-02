import unittest
from unittest.mock import patch
import uuid
import random
import string
from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline
)


class TestMarketPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.shifts = [round(random.uniform(-0.5, 0.5), 2) for _ in range(random.randint(1, 3))]
        self.percentage = round(random.uniform(-0.3, 0.3), 2)
        self.sim_results_mock = {f"shift_{uuid.uuid4().hex[:4]}": random.randint(100, 1000)}
        self.base_report_mock = {"report_id": uuid.uuid4().hex, "status": "active"}
        self.stream_data_mock = [random.randint(0, 100) for _ in range(3)]

    def test_stress_reporter_run_stress_reporting(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as MockGen:
            
            sim_instance = MockSim.return_value
            sim_instance.run_stress_test.return_value = self.sim_results_mock
            
            gen_instance = MockGen.return_value
            gen_instance.generate_symbol_report.return_value = self.base_report_mock
            
            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)
            
            sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)
            
            self.assertEqual(result["simulation_results"], self.sim_results_mock)
            self.assertEqual(result["base_report"], self.base_report_mock)
            self.assertIn(self.symbol, result["compact_text_report"])
            self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
            self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)
            self.assertEqual(result["tabular_report"][0]["results"], self.sim_results_mock)
            self.assertEqual(result["chart_export"]["type"], "line")
            self.assertEqual(result["chart_export"]["data"], self.sim_results_mock)

    def test_stress_reporter_simulate_single_success(self):
        expected_sim = {"percentage": self.percentage, "value": random.randint(500, 5000)}
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator"):
            
            sim_instance = MockSim.return_value
            sim_instance.simulate_scenario.return_value = expected_sim
            
            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)
            
            sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_sim)

    def test_stress_reporter_simulate_single_key_error(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator"):
            
            sim_instance = MockSim.return_value
            sim_instance.simulate_scenario.side_effect = KeyError("missing_key")
            
            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)
            
            sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_stress_reporter_get_stream_data(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator"), \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as MockGen:
            
            gen_instance = MockGen.return_value
            gen_instance.get_raw_stream_dump.return_value = self.stream_data_mock
            
            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()
            
            gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(result, self.stream_data_mock)

    def test_portfolio_stress_reporter_inheritance(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as MockGen:
            
            sim_instance = MockSim.return_value
            sim_instance.run_stress_test.return_value = self.sim_results_mock
            
            gen_instance = MockGen.return_value
            gen_instance.generate_symbol_report.return_value = self.base_report_mock
            
            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)
            
            self.assertEqual(result["simulation_results"], self.sim_results_mock)
            self.assertEqual(result["base_report"], self.base_report_mock)

    def test_generate_stress_report_function(self):
        with patch("skills.market_portfolio_stress_reporter.StressReporter") as MockReporterClass:
            reporter_instance = MockReporterClass.return_value
            expected_output = {"func_result": uuid.uuid4().hex}
            reporter_instance.run_stress_reporting.return_value = expected_output
            
            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
            
            MockReporterClass.assert_called_once_with(self.storage_file)
            reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(result, expected_output)

    def test_run_stress_reporting_pipeline_function(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioStressReporter") as MockPortfolioReporterClass:
            reporter_instance = MockPortfolioReporterClass.return_value
            expected_output = {"pipeline_result": uuid.uuid4().hex}
            reporter_instance.run_stress_report.return_value = expected_output
            
            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
            
            MockPortfolioReporterClass.assert_called_once_with(self.storage_file)
            reporter_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, expected_output)


if __name__ == "__main__":
    unittest.main()