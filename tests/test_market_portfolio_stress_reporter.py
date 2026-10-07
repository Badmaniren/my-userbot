import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [random.uniform(-0.5, 0.5) for _ in range(3)]
        self.percentage = random.uniform(-0.2, 0.2)

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_run_stress_reporting(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_generator = mock_generator_cls.return_value

        expected_sim_results = {uuid.uuid4().hex: random.randint(100, 1000)}
        expected_base_report = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_simulator.run_stress_test.return_value = expected_sim_results
        mock_generator.generate_symbol_report.return_value = expected_base_report

        reporter = StressReporter(self.storage_file)
        result = reporter.run_stress_reporting(self.symbol, self.shifts)

        mock_simulator.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
        mock_generator.generate_symbol_report.assert_called_once_with(self.symbol)

        self.assertEqual(result["simulation_results"], expected_sim_results)
        self.assertEqual(result["base_report"], expected_base_report)
        self.assertIn(self.symbol, result["compact_text_report"])
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)
        self.assertEqual(result["tabular_report"][0]["results"], expected_sim_results)
        self.assertEqual(result["chart_export"]["data"], expected_sim_results)

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_simulate_single_success(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        expected_result = {uuid.uuid4().hex: random.random()}
        mock_simulator.simulate_scenario.return_value = expected_result

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        mock_simulator.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result, expected_result)

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_simulate_single_key_error(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_simulator.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        self.assertEqual(result, {})

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_simulate_single_strict_exception(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        random_exception_msg = uuid.uuid4().hex
        mock_simulator.simulate_scenario.side_effect = RuntimeError(random_exception_msg)

        reporter = StressReporter(self.storage_file)
        with self.assertRaises(RuntimeError) as ctx:
            reporter.simulate_single(self.symbol, self.percentage)
        self.assertIn(random_exception_msg, str(ctx.exception))

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_get_stream_data(self, mock_generator_cls, mock_simulator_cls):
        mock_generator = mock_generator_cls.return_value
        expected_stream = [uuid.uuid4().hex, random.randint(1, 100)]
        mock_generator.get_raw_stream_dump.return_value = expected_stream

        reporter = StressReporter(self.storage_file)
        result = reporter.get_stream_data()

        mock_generator.get_raw_stream_dump.assert_called_once()
        self.assertEqual(result, expected_stream)

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_portfolio_stress_reporter_inheritance(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_generator = mock_generator_cls.return_value

        sim_res = {uuid.uuid4().hex: uuid.uuid4().hex}
        base_rep = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_simulator.run_stress_test.return_value = sim_res
        mock_generator.generate_symbol_report.return_value = base_rep

        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)

        self.assertEqual(result["simulation_results"], sim_res)
        self.assertEqual(result["base_report"], base_rep)

    @patch("skills.market_portfolio_stress_reporter.StressReporter")
    def test_generate_stress_report_helper(self, mock_stress_reporter_cls):
        mock_instance = mock_stress_reporter_cls.return_value
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_instance.run_stress_reporting.return_value = expected_output

        result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

        mock_stress_reporter_cls.assert_called_once_with(self.storage_file)
        mock_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
        self.assertEqual(result, expected_output)

    @patch("skills.market_portfolio_stress_reporter.PortfolioStressReporter")
    def test_run_stress_reporting_pipeline_helper(self, mock_portfolio_reporter_cls):
        mock_instance = mock_portfolio_reporter_cls.return_value
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_instance.run_stress_report.return_value = expected_output

        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

        mock_portfolio_reporter_cls.assert_called_once_with(self.storage_file)
        mock_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
        self.assertEqual(result, expected_output)


if __name__ == "__main__":
    unittest.main()