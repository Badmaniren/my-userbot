import unittest
from unittest.mock import patch
import uuid
import random
import string
from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline
)

class TestMarketPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.shifts = [random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)]
        self.percentage = random.uniform(-1.0, 1.0)
        self.sim_results = {uuid.uuid4().hex: random.random()}
        self.base_report = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.stream_dump = [uuid.uuid4().hex, random.randint(1, 100)]

    def test_stress_reporter_initialization(self):
        reporter = StressReporter(self.storage_file)
        self.assertEqual(reporter.storage_file, self.storage_file)
        self.assertIsNotNone(reporter.simulator)
        self.assertIsNotNone(reporter.generator)

    def test_run_stress_reporting_valid(self):
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test') as mock_sim, \
             patch('skills.market_report_generator.MarketReportGenerator.generate_symbol_report') as mock_gen:
            
            mock_sim.return_value = self.sim_results
            mock_gen.return_value = self.base_report

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertIn("compact_text_report", result)
            self.assertIn("tabular_report", result)
            self.assertIn("chart_export", result)

            self.assertEqual(result["simulation_results"], self.sim_results)
            self.assertEqual(result["base_report"], self.base_report)
            self.assertIn(self.symbol, result["compact_text_report"])
            self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
            self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)
            self.assertEqual(result["tabular_report"][0]["results"], self.sim_results)
            self.assertEqual(result["chart_export"]["data"], self.sim_results)

    def test_simulate_single_success(self):
        expected_sim = {uuid.uuid4().hex: random.randint(100, 500)}
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.simulate_scenario') as mock_sim_single:
            mock_sim_single.return_value = expected_sim

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            self.assertEqual(result, expected_sim)
            mock_sim_single.assert_called_once_with(self.symbol, self.percentage)

    def test_simulate_single_key_error_handling(self):
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.simulate_scenario') as mock_sim_single:
            mock_sim_single.side_effect = KeyError(uuid.uuid4().hex)

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            self.assertEqual(result, {})

    def test_get_stream_data(self):
        with patch('skills.market_report_generator.MarketReportGenerator.get_raw_stream_dump') as mock_stream:
            mock_stream.return_value = self.stream_dump

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            self.assertEqual(result, self.stream_dump)

    def test_portfolio_stress_reporter_inheritance(self):
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test') as mock_sim, \
             patch('skills.market_report_generator.MarketReportGenerator.generate_symbol_report') as mock_gen:
            
            mock_sim.return_value = self.sim_results
            mock_gen.return_value = self.base_report

            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            self.assertEqual(result["simulation_results"], self.sim_results)
            self.assertEqual(result["base_report"], self.base_report)

    def test_generate_stress_report_helper(self):
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test') as mock_sim, \
             patch('skills.market_report_generator.MarketReportGenerator.generate_symbol_report') as mock_gen:
            
            mock_sim.return_value = self.sim_results
            mock_gen.return_value = self.base_report

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            self.assertIn("simulation_results", result)
            self.assertEqual(result["tabular_report"][0]["shifts"], [self.percentage])

    def test_run_stress_reporting_pipeline_helper(self):
        with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.run_stress_test') as mock_sim, \
             patch('skills.market_report_generator.MarketReportGenerator.generate_symbol_report') as mock_gen:
            
            mock_sim.return_value = self.sim_results
            mock_gen.return_value = self.base_report

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            self.assertIn("simulation_results", result)
            self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)


if __name__ == '__main__':
    unittest.main()