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
        self.percentage = round(random.uniform(-0.2, 0.2), 2)

    def test_stress_reporter_initialization(self):
        reporter = StressReporter(self.storage_file)
        self.assertEqual(reporter.storage_file, self.storage_file)
        self.assertIsNotNone(reporter.simulator)
        self.assertIsNotNone(reporter.generator)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_run_stress_reporting(self, mock_generator_class, mock_simulator_class):
        mock_simulator = mock_simulator_class.return_value
        mock_generator = mock_generator_class.return_value

        expected_sim_results = {f"shift_{uuid.uuid4().hex[:4]}": random.randint(100, 1000)}
        expected_base_report = {"report_id": uuid.uuid4().hex, "status": "ok"}

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

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    def test_simulate_single_success(self, mock_simulator_class):
        mock_simulator = mock_simulator_class.return_value
        expected_simulation = {"metric": uuid.uuid4().hex, "value": random.random()}
        mock_simulator.simulate_scenario.return_value = expected_simulation

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        mock_simulator.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result, expected_simulation)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    def test_simulate_single_key_error(self, mock_simulator_class):
        mock_simulator = mock_simulator_class.return_value
        mock_simulator.simulate_scenario.side_effect = KeyError

        reporter = StressReporter(self.storage_file)
        result = reporter.simulate_single(self.symbol, self.percentage)

        mock_simulator.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
        self.assertEqual(result, {})

    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_get_stream_data(self, mock_generator_class):
        mock_generator = mock_generator_class.return_value
        expected_stream = [uuid.uuid4().hex, uuid.uuid4().hex]
        mock_generator.get_raw_stream_dump.return_value = expected_stream

        reporter = StressReporter(self.storage_file)
        result = reporter.get_stream_data()

        mock_generator.get_raw_stream_dump.assert_called_once()
        self.assertEqual(result, expected_stream)

    @patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_reporter.MarketReportGenerator')
    def test_portfolio_stress_reporter_inheritance(self, mock_generator_class, mock_simulator_class):
        mock_simulator = mock_simulator_class.return_value
        mock_generator = mock_generator_class.return_value

        expected_sim_results = {"test": random.randint(1, 100)}
        mock_simulator.run_stress_test.return_value = expected_sim_results
        mock_generator.generate_symbol_report.return_value = {}

        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)

        self.assertEqual(result["simulation_results"], expected_sim_results)

    @patch('skills.market_portfolio_stress_reporter.StressReporter')
    def test_generate_stress_report_function(self, mock_stress_reporter_class):
        mock_reporter_instance = mock_stress_reporter_class.return_value
        expected_output = {"func_test": uuid.uuid4().hex}
        mock_reporter_instance.run_stress_reporting.return_value = expected_output

        result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

        mock_stress_reporter_class.assert_called_once_with(self.storage_file)
        mock_reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
        self.assertEqual(result, expected_output)

    @patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter')
    def test_run_stress_reporting_pipeline_function(self, mock_portfolio_reporter_class):
        mock_reporter_instance = mock_portfolio_reporter_class.return_value
        expected_output = {"pipeline_test": uuid.uuid4().hex}
        mock_reporter_instance.run_stress_report.return_value = expected_output

        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

        mock_portfolio_reporter_class.assert_called_once_with(self.storage_file)
        mock_reporter_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
        self.assertEqual(result, expected_output)


if __name__ == '__main__':
    unittest.main()