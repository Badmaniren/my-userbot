import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline
)


class TestStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.shifts = [round(random.uniform(-50.0, 50.0), 2) for _ in range(random.randint(1, 5))]
        self.percentage = round(random.uniform(-20.0, 20.0), 2)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_run_stress_reporting(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator_instance = mock_simulator_cls.return_value
        mock_generator_instance = mock_generator_cls.return_value

        expected_sim_results = {uuid.uuid4().hex: random.randint(100, 1000)}
        expected_base_report = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_simulator_instance.run_stress_test.return_value = expected_sim_results
        mock_generator_instance.generate_symbol_report.return_value = expected_base_report

        reporter = StressReporter(self.storage_file)
        result = reporter.run_stress_reporting(self.symbol, self.shifts)

        mock_simulator_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
        mock_generator_instance.generate_symbol_report.assert_called_once_with(self.symbol)

        self.assertEqual(result["simulation_results"], expected_sim_results)
        self.assertEqual(result["base_report"], expected_base_report)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_simulate_single_success(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator_instance = mock_simulator_cls.return_value
        expected_simulation = {uuid.uuid4().hex: random.random()}
        mock_simulator_instance.simulate_scenario.return_value = expected_simulation

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        mock_simulator_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result, expected_simulation)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_simulate_single_key_error(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator_instance = mock_simulator_cls.return_value
        mock_simulator_instance.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        mock_simulator_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result, {})

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_get_stream_data(self, mock_generator_cls, mock_simulator_cls):
        mock_generator_instance = mock_generator_cls.return_value
        expected_stream = [uuid.uuid4().hex for _ in range(3)]
        mock_generator_instance.get_raw_stream_dump.return_value = expected_stream

        reporter = StressReporter(self.storage_file)
        result = reporter.get_stream_data()

        mock_generator_instance.get_raw_stream_dump.assert_called_once()
        self.assertEqual(result, expected_stream)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_portfolio_stress_reporter_inheritance(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator_instance = mock_simulator_cls.return_value
        mock_generator_instance = mock_generator_cls.return_value

        expected_sim_results = {uuid.uuid4().hex: random.randint(1, 100)}
        expected_base_report = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_simulator_instance.run_stress_test.return_value = expected_sim_results
        mock_generator_instance.generate_symbol_report.return_value = expected_base_report

        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)

        self.assertEqual(result["simulation_results"], expected_sim_results)
        self.assertEqual(result["base_report"], expected_base_report)

    @patch('skills.market_portfolio_stress_reporter.StressReporter.run_stress_reporting')
    @patch('skills.market_portfolio_stress_reporter.StressReporter')
    def test_generate_stress_report_function(self, mock_reporter_cls, mock_run_stress_reporting):
        mock_reporter_instance = mock_reporter_cls.return_value
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_reporter_instance.run_stress_reporting.return_value = expected_output

        result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

        mock_reporter_cls.assert_called_once_with(self.storage_file)
        mock_reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
        self.assertEqual(result, expected_output)

    @patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter.run_stress_report')
    @patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter')
    def test_run_stress_reporting_pipeline_function(self, mock_portfolio_reporter_cls, mock_run_stress_report):
        mock_reporter_instance = mock_portfolio_reporter_cls.return_value
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_reporter_instance.run_stress_report.return_value = expected_output

        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

        mock_portfolio_reporter_cls.assert_called_once_with(self.storage_file)
        mock_reporter_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
        self.assertEqual(result, expected_output)


if __name__ == '__main__':
    unittest.main()