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


class TestPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.db"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.shifts = [round(random.uniform(-0.5, 0.5), 2) for _ in range(random.randint(1, 3))]
        self.percentage = round(random.uniform(-0.3, 0.3), 2)

    def test_stress_reporter_init(self):
        reporter = StressReporter(self.storage_file)
        self.assertEqual(reporter.storage_file, self.storage_file)
        self.assertIsNotNone(reporter.simulator)
        self.assertIsNotNone(reporter.generator)

    def test_run_stress_reporting(self):
        sim_data = {uuid.uuid4().hex: random.randint(100, 1000)}
        gen_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test') as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report') as mock_gen:
            
            mock_sim.return_value = sim_data
            mock_gen.return_value = gen_data

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim.assert_called_once_with(self.symbol, self.shifts)
            mock_gen.assert_called_once_with(self.symbol)

            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], gen_data)

    def test_simulate_single_success(self):
        expected_output = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.simulate_scenario') as mock_sim:
            mock_sim.return_value = expected_output

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_output)

    def test_simulate_single_key_error(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.simulate_scenario') as mock_sim:
            mock_sim.side_effect = KeyError

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_get_stream_data(self):
        stream_dump = [uuid.uuid4().hex for _ in range(3)]

        with patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.get_raw_stream_dump') as mock_stream:
            mock_stream.return_value = stream_dump

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            mock_stream.assert_called_once()
            self.assertEqual(result, stream_dump)

    def test_portfolio_stress_reporter_inheritance(self):
        sim_data = {uuid.uuid4().hex: random.randint(1, 50)}
        gen_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test') as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report') as mock_gen:
            
            mock_sim.return_value = sim_data
            mock_gen.return_value = gen_data

            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            self.assertIsInstance(reporter, StressReporter)
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], gen_data)

    def test_generate_stress_report_helper(self):
        sim_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        gen_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test') as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report') as mock_gen:
            
            mock_sim.return_value = sim_data
            mock_gen.return_value = gen_data

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_sim.assert_called_once_with(self.symbol, [self.percentage])
            mock_gen.assert_called_once_with(self.symbol)
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], gen_data)

    def test_run_stress_reporting_pipeline_helper(self):
        sim_data = {uuid.uuid4().hex: random.random()}
        gen_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test') as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report') as mock_gen:
            
            mock_sim.return_value = sim_data
            mock_gen.return_value = gen_data

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_sim.assert_called_once_with(self.symbol, self.shifts)
            mock_gen.assert_called_once_with(self.symbol)
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], gen_data)


if __name__ == '__main__':
    unittest.main()