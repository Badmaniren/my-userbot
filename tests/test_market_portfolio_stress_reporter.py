import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline,
    market_portfolio_stress_reporter
)


class TestMarketPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=random.randint(3, 5)))
        self.percentage = round(random.uniform(-0.5, 0.5), 4)
        self.shifts = [round(random.uniform(-0.2, 0.2), 4) for _ in range(random.randint(2, 4))]

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_stress_reporter_initialization(self, mock_generator_cls, mock_simulator_cls):
        reporter = StressReporter(self.storage_file)
        self.assertEqual(reporter.storage_file, self.storage_file)
        mock_simulator_cls.assert_called_once_with(self.storage_file)
        mock_generator_cls.assert_called_once_with(self.storage_file)

    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    def test_run_stress_reporting(self, mock_simulator_cls, mock_generator_cls):
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

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_simulate_single_success(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        expected_sim = {uuid.uuid4().hex: random.random()}
        mock_simulator.simulate_scenario.return_value = expected_sim

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        mock_simulator.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result, expected_sim)

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_simulate_single_key_error(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_simulator.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        mock_simulator.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result, {})

    @patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator")
    @patch("skills.market_portfolio_stress_reporter.MarketReportGenerator")
    def test_get_stream_data(self, mock_generator_cls, mock_simulator_cls):
        mock_generator = mock_generator_cls.return_value
        expected_stream = [uuid.uuid4().hex, uuid.uuid4().hex]
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

        expected_sim_results = {uuid.uuid4().hex: random.random()}
        expected_base_report = {uuid.uuid4().hex: random.random()}

        mock_simulator.run_stress_test.return_value = expected_sim_results
        mock_generator.generate_symbol_report.return_value = expected_base_report

        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)

        self.assertEqual(result["simulation_results"], expected_sim_results)
        self.assertEqual(result["base_report"], expected_base_report)

    @patch("skills.market_portfolio_stress_reporter.StressReporter.run_stress_reporting")
    @patch("skills.market_portfolio_stress_reporter.StressReporter")
    def test_generate_stress_report_function(self, mock_reporter_cls, mock_run_stress_reporting):
        mock_instance = mock_reporter_cls.return_value
        expected_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_instance.run_stress_reporting.return_value = expected_payload

        result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

        mock_reporter_cls.assert_called_once_with(self.storage_file)
        mock_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
        self.assertEqual(result, expected_payload)

    @patch("skills.market_portfolio_stress_reporter.PortfolioStressReporter")
    def test_run_stress_reporting_pipeline_function(self, mock_portfolio_reporter_cls):
        mock_instance = mock_portfolio_reporter_cls.return_value
        expected_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_instance.run_stress_report.return_value = expected_payload

        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

        mock_portfolio_reporter_cls.assert_called_once_with(self.storage_file)
        mock_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
        self.assertEqual(result, expected_payload)

    def test_market_portfolio_stress_reporter_dict_payload(self):
        report_payload = {
            "portfolio_id": "PF-STRESS-01",
            "risk_metrics": {"var": 0.05, "cvar": 0.08, "tax_liability": 500.0},
            "stress_scenarios": [{"scenario_name": "Crash -10%", "impact_multiplier": -0.10}]
        }
        res = market_portfolio_stress_reporter(report_payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["portfolio_id"], "PF-STRESS-01")
        self.assertIn("report_summary", res)


if __name__ == '__main__':
    unittest.main()
