import unittest
from unittest.mock import patch
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
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-30.0, 30.0), 2) for _ in range(random.randint(1, 3))]
        
        self.sim_result_data = {
            "shift": self.shifts[0],
            "impact": uuid.uuid4().hex,
            "value": random.randint(100, 10000)
        }
        self.base_report_data = {
            "symbol": self.symbol,
            "status": uuid.uuid4().hex,
            "metric": random.random()
        }
        self.stream_dump_data = io.BytesIO(uuid.uuid4().bytes)

    def test_stress_reporter_init(self):
        reporter = StressReporter(self.storage_file)
        self.assertEqual(reporter.storage_file, self.storage_file)
        self.assertIsNotNone(reporter.simulator)
        self.assertIsNotNone(reporter.generator)

    def test_run_stress_reporting(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test') as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report') as mock_gen:
            
            mock_sim.return_value = self.sim_result_data
            mock_gen.return_value = self.base_report_data

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim.assert_called_once_with(self.symbol, self.shifts)
            mock_gen.assert_called_once_with(self.symbol)
            
            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertEqual(result["simulation_results"], self.sim_result_data)
            self.assertEqual(result["base_report"], self.base_report_data)

    def test_simulate_single_success(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.simulate_scenario') as mock_sim_single:
            mock_sim_single.return_value = self.sim_result_data

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_single.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, self.sim_result_data)

    def test_simulate_single_key_error(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.simulate_scenario') as mock_sim_single:
            mock_sim_single.side_effect = KeyError(uuid.uuid4().hex)

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_single.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_get_stream_data(self):
        with patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.get_raw_stream_dump') as mock_stream:
            mock_stream.return_value = self.stream_dump_data

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            mock_stream.assert_called_once()
            self.assertEqual(result, self.stream_dump_data)

    def test_portfolio_stress_reporter_inheritance(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test') as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report') as mock_gen:
            
            mock_sim.return_value = self.sim_result_data
            mock_gen.return_value = self.base_report_data

            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            mock_sim.assert_called_once_with(self.symbol, self.shifts)
            mock_gen.assert_called_once_with(self.symbol)
            self.assertEqual(result["simulation_results"], self.sim_result_data)

    def test_generate_stress_report_function(self):
        with patch('skills.market_portfolio_stress_reporter.StressReporter.run_stress_reporting') as mock_run:
            expected_output = {
                uuid.uuid4().hex: uuid.uuid4().hex
            }
            mock_run.return_value = expected_output

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_run.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(result, expected_output)

    def test_run_stress_reporting_pipeline_function(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter.run_stress_report') as mock_run_report:
            expected_output = {
                uuid.uuid4().hex: random.randint(1, 100)
            }
            mock_run_report.return_value = expected_output

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_run_report.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, expected_output)


if __name__ == '__main__':
    unittest.main()