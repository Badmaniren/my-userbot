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


class TestStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(-50.0, -5.0), 2)
        self.shifts = [self.percentage, round(self.percentage / 2, 2)]

    def test_generate_comprehensive_report(self):
        reporter = market_portfolio_stress_reporter()
        pipeline_output = {
            "execution_status": "SUCCESS",
            "portfolio_id": "PF-COMP-100",
            "scenario_results": [
                {"scenario_id": "S1", "pnl": -10000.0, "percentage_change": -5.0},
                {"scenario_id": "S2", "pnl": -50000.0, "percentage_change": -25.0},
                {"scenario_id": "S3", "pnl": -20000.0, "percentage_change": -10.0}
            ]
        }
        report = reporter.generate_comprehensive_report(pipeline_output)
        self.assertEqual(report["portfolio_id"], "PF-COMP-100")
        self.assertEqual(report["worst_case_scenario"]["scenario_id"], "S2")
        self.assertIn("risk_metrics_summary", report)
        self.assertEqual(report["risk_metrics_summary"]["max_drawdown_amount"], 50000.0)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_run_stress_reporting(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_generator = mock_generator_cls.return_value

        expected_sim_result = {self.symbol: random.randint(100, 1000), "shift": self.shifts[0]}
        expected_base_report = {"symbol": self.symbol, "value": random.uniform(1000.0, 50000.0)}

        mock_simulator.run_stress_test.return_value = expected_sim_result
        mock_generator.generate_symbol_report.return_value = expected_base_report

        reporter = StressReporter(self.storage_file)
        result = reporter.run_stress_reporting(self.symbol, self.shifts)

        mock_simulator_cls.assert_called_once_with(self.storage_file)
        mock_generator_cls.assert_called_once_with(self.storage_file)
        mock_simulator.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
        mock_generator.generate_symbol_report.assert_called_once_with(self.symbol)

        self.assertEqual(result["simulation_results"], expected_sim_result)
        self.assertEqual(result["base_report"], expected_base_report)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_simulate_single_success(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        expected_simulation = {"status": uuid.uuid4().hex, "loss": self.percentage}
        mock_simulator.simulate_scenario.return_value = expected_simulation

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        mock_simulator.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result, expected_simulation)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_simulate_single_key_error(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_simulator.simulate_scenario.side_effect = KeyError("Missing symbol")

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        mock_simulator.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result, {})

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_get_stream_data(self, mock_generator_cls, mock_simulator_cls):
        mock_generator = mock_generator_cls.return_value
        expected_stream = [uuid.uuid4().hex, uuid.uuid4().hex]
        mock_generator.get_raw_stream_dump.return_value = expected_stream

        reporter = StressReporter(self.storage_file)
        result = reporter.get_stream_data()

        mock_generator.get_raw_stream_dump.assert_called_once()
        self.assertEqual(result, expected_stream)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_portfolio_stress_reporter_inheritance(self, mock_generator_cls, mock_simulator_cls):
        mock_simulator = mock_simulator_cls.return_value
        mock_generator = mock_generator_cls.return_value

        expected_sim_result = {"chaos_id": uuid.uuid4().hex}
        expected_base_report = {"report_id": uuid.uuid4().hex}

        mock_simulator.run_stress_test.return_value = expected_sim_result
        mock_generator.generate_symbol_report.return_value = expected_base_report

        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)

        self.assertEqual(result["simulation_results"], expected_sim_result)
        self.assertEqual(result["base_report"], expected_base_report)

    @patch('skills.market_portfolio_stress_reporter.StressReporter')
    def test_generate_stress_report_function(self, mock_stress_reporter_cls):
        mock_instance = mock_stress_reporter_cls.return_value
        expected_output = {uuid.uuid4().hex: random.random()}
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