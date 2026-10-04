import unittest
from unittest.mock import patch, MagicMock
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
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.shifts = [round(random.uniform(-0.5, 0.5), 4) for _ in range(random.randint(1, 3))]
        self.percentage = round(random.uniform(-0.3, 0.3), 4)
        self.sim_results_mock = {uuid.uuid4().hex: random.random()}
        self.base_report_mock = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.stream_dump_mock = [uuid.uuid4().hex for _ in range(3)]

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_stress_reporter_initialization(self, mock_generator_cls, mock_simulator_cls):
        reporter = StressReporter(self.storage_file)
        mock_simulator_cls.assert_called_once_with(self.storage_file)
        mock_generator_cls.assert_called_once_with(self.storage_file)
        self.assertEqual(reporter.storage_file, self.storage_file)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_run_stress_reporting(self, mock_generator_cls, mock_simulator_cls):
        sim_instance = mock_simulator_cls.return_value
        sim_instance.run_stress_test.return_value = self.sim_results_mock

        gen_instance = mock_generator_cls.return_value
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

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_simulate_single_success(self, mock_generator_cls, mock_simulator_cls):
        sim_instance = mock_simulator_cls.return_value
        expected_output = {uuid.uuid4().hex: random.randint(100, 999)}
        sim_instance.simulate_scenario.return_value = expected_output

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result, expected_output)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_simulate_single_key_error(self, mock_generator_cls, mock_simulator_cls):
        sim_instance = mock_simulator_cls.return_value
        sim_instance.simulate_scenario.side_effect = KeyError("Missing symbol")

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result, {})

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_get_stream_data(self, mock_generator_cls, mock_simulator_cls):
        gen_instance = mock_generator_cls.return_value
        gen_instance.get_raw_stream_dump.return_value = self.stream_dump_mock

        reporter = StressReporter(self.storage_file)
        result = reporter.get_stream_data()

        gen_instance.get_raw_stream_dump.assert_called_once()
        self.assertEqual(result, self.stream_dump_mock)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_portfolio_stress_reporter_run_stress_report(self, mock_generator_cls, mock_simulator_cls):
        sim_instance = mock_simulator_cls.return_value
        sim_instance.run_stress_test.return_value = self.sim_results_mock

        gen_instance = mock_generator_cls.return_value
        gen_instance.generate_symbol_report.return_value = self.base_report_mock

        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)

        self.assertEqual(result["simulation_results"], self.sim_results_mock)
        self.assertEqual(result["base_report"], self.base_report_mock)

    @patch('skills.market_portfolio_stress_reporter.StressReporter')
    def test_generate_stress_report_function(self, mock_stress_reporter_cls):
        reporter_instance = mock_stress_reporter_cls.return_value
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        reporter_instance.run_stress_reporting.return_value = expected_dict

        result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

        mock_stress_reporter_cls.assert_called_once_with(self.storage_file)
        reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
        self.assertEqual(result, expected_dict)

    @patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter')
    def test_run_stress_reporting_pipeline_function(self, mock_portfolio_reporter_cls):
        reporter_instance = mock_portfolio_reporter_cls.return_value
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        reporter_instance.run_stress_report.return_value = expected_dict

        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

        mock_portfolio_reporter_cls.assert_called_once_with(self.storage_file)
        reporter_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
        self.assertEqual(result, expected_dict)


if __name__ == '__main__':
    unittest.main()