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

    def test_run_stress_reporting(self):
        sim_result_mock = {uuid.uuid4().hex: random.randint(100, 1000)}
        base_report_mock = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', return_value=sim_result_mock) as mock_sim, \
             patch('skills.market_report_generator.MarketReportGenerator.generate_symbol_report', return_value=base_report_mock) as mock_gen:

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim.assert_called_once_with(self.symbol, self.shifts)
            mock_gen.assert_called_once_with(self.symbol)

            self.assertEqual(result["simulation_results"], sim_result_mock)
            self.assertEqual(result["base_report"], base_report_mock)
            self.assertIn(self.symbol, result["compact_text_report"])
            self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
            self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)
            self.assertEqual(result["tabular_report"][0]["results"], sim_result_mock)
            self.assertEqual(result["chart_export"]["type"], "line")
            self.assertEqual(result["chart_export"]["data"], sim_result_mock)

    def test_simulate_single_success(self):
        expected_output = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.simulate_scenario', return_value=expected_output) as mock_sim:
            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_output)

    def test_simulate_single_key_error(self):
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.simulate_scenario', side_effect=KeyError) as mock_sim:
            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_get_stream_data(self):
        stream_dump_mock = [uuid.uuid4().hex, uuid.uuid4().hex]

        with patch('skills.market_report_generator.MarketReportGenerator.get_raw_stream_dump', return_value=stream_dump_mock) as mock_stream:
            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            mock_stream.assert_called_once()
            self.assertEqual(result, stream_dump_mock)

    def test_portfolio_stress_reporter_inheritance(self):
        sim_result_mock = {uuid.uuid4().hex: uuid.uuid4().hex}
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', return_value=sim_result_mock):
            with patch('skills.market_report_generator.MarketReportGenerator.generate_symbol_report', return_value={}):
                reporter = PortfolioStressReporter(self.storage_file)
                result = reporter.run_stress_report(self.symbol, self.shifts)
                self.assertEqual(result["simulation_results"], sim_result_mock)

    def test_generate_stress_report_helper(self):
        sim_result_mock = {uuid.uuid4().hex: random.randint(1, 500)}
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', return_value=sim_result_mock) as mock_sim:
            with patch('skills.market_report_generator.MarketReportGenerator.generate_symbol_report', return_value={}):
                result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
                mock_sim.assert_called_once_with(self.symbol, [self.percentage])
                self.assertEqual(result["simulation_results"], sim_result_mock)

    def test_run_stress_reporting_pipeline_helper(self):
        sim_result_mock = {uuid.uuid4().hex: random.randint(501, 1000)}
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test', return_value=sim_result_mock) as mock_sim:
            with patch('skills.market_report_generator.MarketReportGenerator.generate_symbol_report', return_value={}):
                result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
                mock_sim.assert_called_once_with(self.symbol, self.shifts)
                self.assertEqual(result["simulation_results"], sim_result_mock)


if __name__ == '__main__':
    unittest.main()