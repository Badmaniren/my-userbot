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


class TestStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.shifts = [round(random.uniform(-0.5, 0.5), 4) for _ in range(random.randint(1, 3))]
        self.percentage = round(random.uniform(-0.2, 0.2), 4)
        self.mock_sim_results = {uuid.uuid4().hex: random.randint(100, 1000)}
        self.mock_base_report = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_stream_dump = [uuid.uuid4().hex for _ in range(3)]

    def test_run_stress_reporting(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            instance_sim = MockSim.return_value
            instance_sim.run_stress_test.return_value = self.mock_sim_results
            
            instance_gen = MockGen.return_value
            instance_gen.generate_symbol_report.return_value = self.mock_base_report

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            instance_sim.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            instance_gen.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertEqual(result["simulation_results"], self.mock_sim_results)
            self.assertEqual(result["base_report"], self.mock_base_report)
            self.assertIn(self.symbol, result["compact_text_report"])
            self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
            self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)
            self.assertEqual(result["tabular_report"][0]["results"], self.mock_sim_results)
            self.assertEqual(result["chart_export"]["type"], "line")
            self.assertEqual(result["chart_export"]["data"], self.mock_sim_results)

    def test_simulate_single_success(self):
        expected_sim_value = {uuid.uuid4().hex: random.random()}
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim:
            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.return_value = expected_sim_value

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            instance_sim.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_sim_value)

    def test_simulate_single_key_error(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim:
            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            instance_sim.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_get_stream_data(self):
        with patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            instance_gen = MockGen.return_value
            instance_gen.get_raw_stream_dump.return_value = self.mock_stream_dump

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            instance_gen.get_raw_stream_dump.assert_called_once()
            self.assertEqual(result, self.mock_stream_dump)

    def test_portfolio_stress_reporter_inheritance(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            instance_sim = MockSim.return_value
            instance_sim.run_stress_test.return_value = self.mock_sim_results
            instance_gen = MockGen.return_value
            instance_gen.generate_symbol_report.return_value = self.mock_base_report

            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            self.assertEqual(result["simulation_results"], self.mock_sim_results)
            self.assertEqual(result["base_report"], self.mock_base_report)

    def test_generate_stress_report_function(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            instance_sim = MockSim.return_value
            instance_sim.run_stress_test.return_value = self.mock_sim_results
            instance_gen = MockGen.return_value
            instance_gen.generate_symbol_report.return_value = self.mock_base_report

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            instance_sim.run_stress_test.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(result["simulation_results"], self.mock_sim_results)

    def test_run_stress_reporting_pipeline_function(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            instance_sim = MockSim.return_value
            instance_sim.run_stress_test.return_value = self.mock_sim_results
            instance_gen = MockGen.return_value
            instance_gen.generate_symbol_report.return_value = self.mock_base_report

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            instance_sim.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result["simulation_results"], self.mock_sim_results)


if __name__ == '__main__':
    unittest.main()