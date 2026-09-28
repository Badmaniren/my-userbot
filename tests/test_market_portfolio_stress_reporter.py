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
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(-50.0, -5.0), 2)
        self.shifts = [self.percentage, round(self.percentage * 1.5, 2)]

    def test_stress_reporter_initialization(self):
        reporter = StressReporter(self.storage_file)
        self.assertEqual(reporter.storage_file, self.storage_file)
        self.assertIsNotNone(reporter.simulator)
        self.assertIsNotNone(reporter.generator)

    def test_run_stress_reporting(self):
        sim_data = {uuid.uuid4().hex: random.uniform(10.0, 100.0)}
        report_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test") as mock_sim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report") as mock_gen:
            
            mock_sim.return_value = sim_data
            mock_gen.return_value = report_data

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim.assert_called_once_with(self.symbol, self.shifts)
            mock_gen.assert_called_once_with(self.symbol)

            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], report_data)

    def test_simulate_single_success(self):
        expected_result = {uuid.uuid4().hex: random.randint(1, 1000)}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.simulate_scenario") as mock_simulate:
            mock_simulate.return_value = expected_result

            reporter = StressReporter(self.storage_file)
            res = reporter.simulate_single(self.symbol, self.percentage)

            mock_simulate.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(res, expected_result)

    def test_simulate_single_key_error(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.simulate_scenario") as mock_simulate:
            mock_simulate.side_effect = KeyError("Missing symbol")

            reporter = StressReporter(self.storage_file)
            res = reporter.simulate_single(self.symbol, self.percentage)

            mock_simulate.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(res, {})

    def test_get_stream_data(self):
        raw_dump = [uuid.uuid4().hex, random.randint(100, 500)]

        with patch("skills.market_portfolio_stress_reporter.MarketReportGenerator.get_raw_stream_dump") as mock_dump:
            mock_dump.return_value = raw_dump

            reporter = StressReporter(self.storage_file)
            res = reporter.get_stream_data()

            mock_dump.assert_called_once()
            self.assertEqual(res, raw_dump)

    def test_portfolio_stress_reporter_inheritance(self):
        sim_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        report_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test") as mock_sim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report") as mock_gen:
            
            mock_sim.return_value = sim_data
            mock_gen.return_value = report_data

            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], report_data)

    def test_generate_stress_report_function(self):
        sim_data = {uuid.uuid4().hex: random.random()}
        report_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test") as mock_sim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report") as mock_gen:
            
            mock_sim.return_value = sim_data
            mock_gen.return_value = report_data

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_sim.assert_called_once_with(self.symbol, [self.percentage])
            mock_gen.assert_called_once_with(self.symbol)
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], report_data)

    def test_run_stress_reporting_pipeline_function(self):
        sim_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        report_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test") as mock_sim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report") as mock_gen:
            
            mock_sim.return_value = sim_data
            mock_gen.return_value = report_data

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_sim.assert_called_once_with(self.symbol, self.shifts)
            mock_gen.assert_called_once_with(self.symbol)
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], report_data)

if __name__ == "__main__":
    unittest.main()