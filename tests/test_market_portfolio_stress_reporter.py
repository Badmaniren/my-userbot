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
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.shifts = [round(random.uniform(-0.5, 0.5), 2) for _ in range(3)]
        self.percentage = round(random.uniform(-0.2, 0.2), 2)

    def test_stress_reporter_initialization(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen:
            
            reporter = StressReporter(self.storage_file)
            
            self.assertEqual(reporter.storage_file, self.storage_file)
            mock_sim.assert_called_once_with(self.storage_file)
            mock_gen.assert_called_once_with(self.storage_file)

    def test_run_stress_reporting_contract(self):
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

            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertIn("compact_text_report", result)
            self.assertIn("tabular_report", result)
            self.assertIn("chart_export", result)

            self.assertEqual(result["simulation_results"], expected_sim_results)
            self.assertEqual(result["base_report"], expected_base_report)
            self.assertIn(self.symbol, result["compact_text_report"])
            self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
            self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)
            self.assertEqual(result["tabular_report"][0]["results"], expected_sim_results)
            self.assertEqual(result["chart_export"]["data"], expected_sim_results)

    def test_simulate_single_success(self):
        expected_simulation = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = expected_simulation

            reporter = StressReporter(self.storage_file)
            res = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(res, expected_simulation)

    def test_simulate_single_key_error_handling(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)

            reporter = StressReporter(self.storage_file)
            res = reporter.simulate_single(self.symbol, self.percentage)

            self.assertEqual(res, {})

    def test_simulate_single_unexpected_exception_raises(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = RuntimeError(uuid.uuid4().hex)

            reporter = StressReporter(self.storage_file)
            with self.assertRaises(RuntimeError):
                reporter.simulate_single(self.symbol, self.percentage)

    def test_get_stream_data(self):
        expected_stream = [uuid.uuid4().hex for _ in range(3)]

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator'), \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen_cls:
            
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = expected_stream

            reporter = StressReporter(self.storage_file)
            stream = reporter.get_stream_data()

            mock_gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(stream, expected_stream)


class TestPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.shifts = [round(random.uniform(-1.0, 1.0), 2)]

    def test_portfolio_stress_reporter_inheritance_and_execution(self):
        expected_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(PortfolioStressReporter, 'run_stress_reporting', return_value=expected_data) as mock_reporting:
            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            mock_reporting.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, expected_data)


class TestStandaloneFunctions(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=6))
        self.percentage = round(random.uniform(-0.5, 0.5), 2)
        self.shifts = [self.percentage]

    def test_generate_stress_report(self):
        expected_output = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch('skills.market_portfolio_stress_reporter.StressReporter') as mock_reporter_cls:
            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.run_stress_reporting.return_value = expected_output

            res = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_reporter_cls.assert_called_once_with(self.storage_file)
            mock_reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(res, expected_output)

    def test_run_stress_reporting_pipeline(self):
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter') as mock_portfolio_cls:
            mock_portfolio_instance = mock_portfolio_cls.return_value
            mock_portfolio_instance.run_stress_report.return_value = expected_output

            res = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_portfolio_cls.assert_called_once_with(self.storage_file)
            mock_portfolio_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(res, expected_output)


if __name__ == '__main__':
    unittest.main()