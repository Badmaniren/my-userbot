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


class TestMarketPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)]
        self.percentage = random.uniform(-0.2, 0.2)

    def test_stress_reporter_init(self):
        reporter = StressReporter(self.storage_file)
        self.assertEqual(reporter.storage_file, self.storage_file)
        self.assertIsNotNone(reporter.simulator)
        self.assertIsNotNone(reporter.generator)

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_run_stress_reporting(self, mock_generator_cls, mock_simulator_cls):
        mock_sim_instance = mock_simulator_cls.return_value
        mock_gen_instance = mock_generator_cls.return_value

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

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_simulate_single(self, mock_generator_cls, mock_simulator_cls):
        mock_sim_instance = mock_simulator_cls.return_value
        expected_simulation = {uuid.uuid4().hex: random.random()}
        mock_sim_instance.simulate_scenario.return_value = expected_simulation

        reporter = StressReporter(self.storage_file)
        res = reporter.simulate_single(self.symbol, self.percentage)

        mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(res, expected_simulation)

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_get_stream_data(self, mock_generator_cls, mock_simulator_cls):
        mock_gen_instance = mock_generator_cls.return_value
        expected_stream = [uuid.uuid4().hex, uuid.uuid4().hex]
        mock_gen_instance.get_raw_stream_dump.return_value = expected_stream

        reporter = StressReporter(self.storage_file)
        res = reporter.get_stream_data()

        mock_gen_instance.get_raw_stream_dump.assert_called_once()
        self.assertEqual(res, expected_stream)

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_portfolio_stress_reporter_inheritance(self, mock_generator_cls, mock_simulator_cls):
        mock_sim_instance = mock_simulator_cls.return_value
        mock_gen_instance = mock_generator_cls.return_value

        expected_sim_results = {uuid.uuid4().hex: random.randint(1, 50)}
        mock_sim_instance.run_stress_test.return_value = expected_sim_results

        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)

        self.assertEqual(result["simulation_results"], expected_sim_results)

    @patch("skills.market_portfolio_stress_reporter.StressReporter")
    def test_generate_stress_report_helper(self, mock_stress_reporter_cls):
        mock_instance = mock_stress_reporter_cls.return_value
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_instance.run_stress_reporting.return_value = expected_dict

        res = generate_stress_report(self.storage_file, self.symbol, self.percentage)

        mock_stress_reporter_cls.assert_called_once_with(self.storage_file)
        mock_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
        self.assertEqual(res, expected_dict)

    @patch("skills.market_portfolio_stress_reporter.PortfolioStressReporter")
    def test_run_stress_reporting_pipeline_helper(self, mock_portfolio_reporter_cls):
        mock_instance = mock_portfolio_reporter_cls.return_value
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_instance.run_stress_report.return_value = expected_dict

        res = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

        mock_portfolio_reporter_cls.assert_called_once_with(self.storage_file)
        mock_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
        self.assertEqual(res, expected_dict)

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    def test_error_handling_no_suppression(self, mock_simulator_cls):
        mock_sim_instance = mock_simulator_cls.return_value
        err_msg = f"critical_failure_{uuid.uuid4().hex}"
        mock_sim_instance.run_stress_test.side_effect = RuntimeError(err_msg)

        reporter = StressReporter(self.storage_file)
        with self.assertRaises(RuntimeError) as ctx:
            reporter.run_stress_reporting(self.symbol, self.shifts)
        
        self.assertIn(err_msg, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()