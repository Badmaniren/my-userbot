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


class TestMarketPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.shifts = [random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)]
        self.percentage = random.uniform(-0.2, 0.2)

    def test_stress_reporter_initialization(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen:
            
            reporter = StressReporter(self.storage_file)
            
            self.assertEqual(reporter.storage_file, self.storage_file)
            mock_sim.assert_called_once_with(self.storage_file)
            mock_gen.assert_called_once_with(self.storage_file)

    def test_run_stress_reporting_success(self):
        expected_sim_results = {uuid.uuid4().hex: random.randint(100, 1000)}
        expected_base_report = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = expected_sim_results

            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.return_value = expected_base_report

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            mock_gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertEqual(result["simulation_results"], expected_sim_results)
            self.assertEqual(result["base_report"], expected_base_report)
            self.assertEqual(result["compact_text_report"], f"Stress Report for {self.symbol}: Shifts={self.shifts}")
            self.assertEqual(result["tabular_report"], [{"symbol": self.symbol, "shifts": self.shifts, "results": expected_sim_results}])
            self.assertEqual(result["chart_export"], {"type": "line", "data": expected_sim_results})

    def test_simulate_single_success(self):
        expected_simulation = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls:
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = expected_simulation

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_simulation)

    def test_simulate_single_key_error_propagation(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls:
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)

            reporter = StressReporter(self.storage_file)
            
            with self.assertRaises(KeyError):
                reporter.simulate_single(self.symbol, self.percentage)

    def test_get_stream_data(self):
        expected_stream = [uuid.uuid4().hex, random.randint(1, 100)]

        with patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen_cls:
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = expected_stream

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            mock_gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(result, expected_stream)

    def test_portfolio_stress_reporter_inheritance(self):
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(StressReporter, 'run_stress_reporting', return_value=expected_result) as mock_run:
            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            mock_run.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, expected_result)

    def test_generate_stress_report_helper(self):
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.StressReporter.run_stress_reporting', return_value=expected_result) as mock_run:
            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_run.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(result, expected_result)

    def test_run_stress_reporting_pipeline_helper(self):
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter.run_stress_report', return_value=expected_result) as mock_run:
            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_run.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()