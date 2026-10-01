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

class TestStressReporter(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.shift_val = round(random.uniform(-0.5, 0.5), 4)
        self.shifts = [self.shift_val]

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_run_stress_reporting(self, mock_generator_cls, mock_simulator_cls):
        mock_sim_instance = mock_simulator_cls.return_value
        mock_gen_instance = mock_generator_cls.return_value

        expected_sim_result = {uuid.uuid4().hex: random.randint(100, 1000)}
        expected_base_report = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_sim_instance.run_stress_test.return_value = expected_sim_result
        mock_gen_instance.generate_symbol_report.return_value = expected_base_report

        reporter = StressReporter(self.storage_file)
        result = reporter.run_stress_reporting(self.symbol, self.shifts)

        mock_simulator_cls.assert_called_once_with(self.storage_file)
        mock_generator_cls.assert_called_once_with(self.storage_file)
        mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
        mock_gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)

        self.assertEqual(result["simulation_results"], expected_sim_result)
        self.assertEqual(result["base_report"], expected_base_report)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_simulate_single_success(self, mock_generator_cls, mock_simulator_cls):
        mock_sim_instance = mock_simulator_cls.return_value
        expected_sim = {uuid.uuid4().hex: random.random()}
        mock_sim_instance.simulate_scenario.return_value = expected_sim

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.shift_val)

        mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.shift_val)
        self.assertEqual(result, expected_sim)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_simulate_single_key_error(self, mock_generator_cls, mock_simulator_cls):
        mock_sim_instance = mock_simulator_cls.return_value
        mock_sim_instance.simulate_scenario.side_effect = KeyError

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.shift_val)

        mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.shift_val)
        self.assertEqual(result, {})

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_get_stream_data(self, mock_generator_cls, mock_simulator_cls):
        mock_gen_instance = mock_generator_cls.return_value
        expected_stream = [uuid.uuid4().hex, uuid.uuid4().hex]
        mock_gen_instance.get_raw_stream_dump.return_value = expected_stream

        reporter = StressReporter(self.storage_file)
        result = reporter.get_stream_data()

        mock_gen_instance.get_raw_stream_dump.assert_called_once()
        self.assertEqual(result, expected_stream)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_portfolio_stress_reporter_inheritance(self, mock_generator_cls, mock_simulator_cls):
        mock_sim_instance = mock_simulator_cls.return_value
        mock_gen_instance = mock_generator_cls.return_value

        expected_sim_result = {uuid.uuid4().hex: random.randint(1, 50)}
        expected_base_report = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_sim_instance.run_stress_test.return_value = expected_sim_result
        mock_gen_instance.generate_symbol_report.return_value = expected_base_report

        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)

        self.assertEqual(result["simulation_results"], expected_sim_result)
        self.assertEqual(result["base_report"], expected_base_report)

    @patch('skills.market_portfolio_stress_reporter.StressReporter')
    def test_generate_stress_report_helper(self, mock_stress_reporter_cls):
        mock_reporter_instance = mock_stress_reporter_cls.return_value
        expected_return = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_reporter_instance.run_stress_reporting.return_value = expected_return

        result = generate_stress_report(self.storage_file, self.symbol, self.shift_val)

        mock_stress_reporter_cls.assert_called_once_with(self.storage_file)
        mock_reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.shift_val])
        self.assertEqual(result, expected_return)

    @patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter')
    def test_run_stress_reporting_pipeline_helper(self, mock_portfolio_reporter_cls):
        mock_reporter_instance = mock_portfolio_reporter_cls.return_value
        expected_return = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_reporter_instance.run_stress_report.return_value = expected_return

        shifts = [self.shift_val, round(self.shift_val * 2, 4)]
        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, shifts)

        mock_portfolio_reporter_cls.assert_called_once_with(self.storage_file)
        mock_reporter_instance.run_stress_report.assert_called_once_with(self.symbol, shifts)
        self.assertEqual(result, expected_return)

if __name__ == '__main__':
    unittest.main()