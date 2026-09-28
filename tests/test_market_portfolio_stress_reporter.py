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
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=random.randint(3, 5)))
        self.percentage = round(random.uniform(-0.5, 0.5), 4)
        self.shifts = [round(random.uniform(-0.3, 0.3), 4) for _ in range(random.randint(2, 4))]

    def test_stress_reporter_initialization(self):
        reporter = StressReporter(self.storage_file)
        self.assertEqual(reporter.storage_file, self.storage_file)
        self.assertIsNotNone(reporter.simulator)
        self.assertIsNotNone(reporter.generator)

    def test_run_stress_reporting(self):
        sim_mock_result = {uuid.uuid4().hex: random.uniform(10.0, 100.0)}
        gen_mock_result = {uuid.uuid4().hex: random.randint(1000, 5000)}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test', return_value=sim_mock_result) as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report', return_value=gen_mock_result) as mock_gen:
            
            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim.assert_called_once_with(self.symbol, self.shifts)
            mock_gen.assert_called_once_with(self.symbol)

            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertEqual(result["simulation_results"], sim_mock_result)
            self.assertEqual(result["base_report"], gen_mock_result)

    def test_simulate_single_success(self):
        expected_output = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.simulate_scenario', return_value=expected_output) as mock_sim:
            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_output)

    def test_simulate_single_key_error(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.simulate_scenario', side_effect=KeyError):
            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_get_stream_data(self):
        raw_dump = [uuid.uuid4().hex for _ in range(3)]

        with patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.get_raw_stream_dump', return_value=raw_dump) as mock_dump:
            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            mock_dump.assert_called_once()
            self.assertEqual(result, raw_dump)

    def test_portfolio_stress_reporter_inheritance(self):
        reporter = PortfolioStressReporter(self.storage_file)
        self.assertIsInstance(reporter, StressReporter)

        sim_mock_result = {uuid.uuid4().hex: random.randint(1, 100)}
        gen_mock_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test', return_value=sim_mock_result), \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report', return_value=gen_mock_result):
            
            result = reporter.run_stress_report(self.symbol, self.shifts)
            self.assertEqual(result["simulation_results"], sim_mock_result)
            self.assertEqual(result["base_report"], gen_mock_result)

    def test_generate_stress_report_helper(self):
        sim_mock_result = {uuid.uuid4().hex: random.uniform(-10, 10)}
        gen_mock_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test', return_value=sim_mock_result) as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report', return_value=gen_mock_result) as mock_gen:
            
            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_sim.assert_called_once_with(self.symbol, [self.percentage])
            mock_gen.assert_called_once_with(self.symbol)
            self.assertEqual(result["simulation_results"], sim_mock_result)
            self.assertEqual(result["base_report"], gen_mock_result)

    def test_run_stress_reporting_pipeline_helper(self):
        sim_mock_result = {uuid.uuid4().hex: random.random()}
        gen_mock_result = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test', return_value=sim_mock_result) as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report', return_value=gen_mock_result) as mock_gen:
            
            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_sim.assert_called_once_with(self.symbol, self.shifts)
            mock_gen.assert_called_once_with(self.symbol)
            self.assertEqual(result["simulation_results"], sim_mock_result)
            self.assertEqual(result["base_report"], gen_mock_result)


if __name__ == '__main__':
    unittest.main()