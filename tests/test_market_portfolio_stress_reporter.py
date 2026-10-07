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


class TestPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.shifts = [round(random.uniform(-0.5, 0.5), 2) for _ in range(random.randint(1, 3))]
        self.percentage = round(random.uniform(-1.0, 1.0), 2)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_run_stress_reporting_success(self, mock_report_gen_cls, mock_sim_cls):
        mock_sim_instance = mock_sim_cls.return_value
        mock_gen_instance = mock_report_gen_cls.return_value

        expected_sim_results = {uuid.uuid4().hex: random.randint(100, 1000)}
        expected_base_report = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_sim_instance.run_stress_test.return_value = expected_sim_results
        mock_gen_instance.generate_symbol_report.return_value = expected_base_report

        reporter = StressReporter(self.storage_file)
        result = reporter.run_stress_reporting(self.symbol, self.shifts)

        mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
        mock_gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)

        self.assertEqual(result["simulation_results"], expected_sim_results)
        self.assertEqual(result["base_report"], expected_base_report)
        self.assertIn(self.symbol, result["compact_text_report"])
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)
        self.assertEqual(result["tabular_report"][0]["results"], expected_sim_results)
        self.assertEqual(result["chart_export"]["type"], "line")
        self.assertEqual(result["chart_export"]["data"], expected_sim_results)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_simulate_single_success(self, mock_report_gen_cls, mock_sim_cls):
        mock_sim_instance = mock_sim_cls.return_value
        expected_sim_single = {uuid.uuid4().hex: random.random()}
        mock_sim_instance.simulate_scenario.return_value = expected_sim_single

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result, expected_sim_single)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_simulate_single_key_error(self, mock_report_gen_cls, mock_sim_cls):
        mock_sim_instance = mock_sim_cls.return_value
        mock_sim_instance.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        self.assertEqual(result, {})

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_get_stream_data(self, mock_report_gen_cls, mock_sim_cls):
        mock_gen_instance = mock_report_gen_cls.return_value
        expected_stream = [uuid.uuid4().hex, random.randint(1, 100)]
        mock_gen_instance.get_raw_stream_dump.return_value = expected_stream

        reporter = StressReporter(self.storage_file)
        result = reporter.get_stream_data()

        mock_gen_instance.get_raw_stream_dump.assert_called_once()
        self.assertEqual(result, expected_stream)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_portfolio_stress_reporter_inheritance(self, mock_report_gen_cls, mock_sim_cls):
        mock_sim_instance = mock_sim_cls.return_value
        mock_gen_instance = mock_report_gen_cls.return_value

        expected_sim_results = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_sim_instance.run_stress_test.return_value = expected_sim_results
        mock_gen_instance.generate_symbol_report.return_value = {}

        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)

        self.assertEqual(result["simulation_results"], expected_sim_results)

    @patch('skills.market_portfolio_stress_reporter.StressReporter')
    def test_generate_stress_report_function(self, mock_stress_reporter_cls):
        mock_instance = mock_stress_reporter_cls.return_value
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_instance.run_stress_reporting.return_value = expected_output

        result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

        mock_stress_reporter_cls.assert_called_once_with(self.storage_file)
        mock_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
        self.assertEqual(result, expected_output)

    @patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter')
    def test_run_stress_reporting_pipeline_function(self, mock_portfolio_reporter_cls):
        mock_instance = mock_portfolio_reporter_cls.return_value
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_instance.run_stress_report.return_value = expected_output

        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

        mock_portfolio_reporter_cls.assert_called_once_with(self.storage_file)
        mock_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
        self.assertEqual(result, expected_output)


if __name__ == '__main__':
    unittest.main()