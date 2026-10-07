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
        self.storage_file = f"store_{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.shifts = [round(random.uniform(-0.5, 0.5), 2) for _ in range(random.randint(1, 4))]
        self.percentage = round(random.uniform(-1.0, 1.0), 2)
        self.sim_output = {uuid.uuid4().hex: random.randint(100, 999)}
        self.base_report_output = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.stream_dump_output = [uuid.uuid4().hex for _ in range(3)]

    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    def test_run_stress_reporting_success(self, mock_simulator_cls, mock_generator_cls):
        mock_sim_instance = mock_simulator_cls.return_value
        mock_sim_instance.run_stress_test.return_value = self.sim_output

        mock_gen_instance = mock_generator_cls.return_value
        mock_gen_instance.generate_symbol_report.return_value = self.base_report_output

        reporter = StressReporter(self.storage_file)
        result = reporter.run_stress_reporting(self.symbol, self.shifts)

        mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
        mock_gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)

        self.assertEqual(result["simulation_results"], self.sim_output)
        self.assertEqual(result["base_report"], self.base_report_output)
        self.assertEqual(result["compact_text_report"], f"Stress Report for {self.symbol}: Shifts={self.shifts}")
        self.assertEqual(result["tabular_report"], [{"symbol": self.symbol, "shifts": self.shifts, "results": self.sim_output}])
        self.assertEqual(result["chart_export"], {"type": "line", "data": self.sim_output})

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    def test_simulate_single_success(self, mock_simulator_cls):
        mock_sim_instance = mock_simulator_cls.return_value
        expected_res = {uuid.uuid4().hex: random.random()}
        mock_sim_instance.simulate_scenario.return_value = expected_res

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result, expected_res)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    def test_simulate_single_key_error(self, mock_simulator_cls):
        mock_sim_instance = mock_simulator_cls.return_value
        mock_sim_instance.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        self.assertEqual(result, {})

    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    def test_get_stream_data(self, mock_simulator_cls, mock_generator_cls):
        mock_gen_instance = mock_generator_cls.return_value
        mock_gen_instance.get_raw_stream_dump.return_value = self.stream_dump_output

        reporter = StressReporter(self.storage_file)
        result = reporter.get_stream_data()

        mock_gen_instance.get_raw_stream_dump.assert_called_once()
        self.assertEqual(result, self.stream_dump_output)

    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    def test_portfolio_stress_reporter_inheritance(self, mock_simulator_cls, mock_generator_cls):
        mock_sim_instance = mock_simulator_cls.return_value
        mock_sim_instance.run_stress_test.return_value = self.sim_output
        mock_gen_instance = mock_generator_cls.return_value
        mock_gen_instance.generate_symbol_report.return_value = self.base_report_output

        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)

        self.assertEqual(result["simulation_results"], self.sim_output)

    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    def test_generate_stress_report_helper(self, mock_simulator_cls, mock_generator_cls):
        mock_sim_instance = mock_simulator_cls.return_value
        mock_sim_instance.run_stress_test.return_value = self.sim_output
        mock_gen_instance = mock_generator_cls.return_value
        mock_gen_instance.generate_symbol_report.return_value = self.base_report_output

        result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

        mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, [self.percentage])
        self.assertEqual(result["tabular_report"][0]["shifts"], [self.percentage])

    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    def test_run_stress_reporting_pipeline_helper(self, mock_simulator_cls, mock_generator_cls):
        mock_sim_instance = mock_simulator_cls.return_value
        mock_sim_instance.run_stress_test.return_value = self.sim_output
        mock_gen_instance = mock_generator_cls.return_value
        mock_gen_instance.generate_symbol_report.return_value = self.base_report_output

        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

        mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
        self.assertEqual(result["simulation_results"], self.sim_output)


if __name__ == '__main__':
    unittest.main()