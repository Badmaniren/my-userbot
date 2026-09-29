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
        self.shifts = [random.uniform(-0.5, 0.5) for _ in range(3)]
        self.percentage = random.uniform(-0.3, 0.3)

    def test_stress_reporter_init(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen:
            
            reporter = StressReporter(self.storage_file)
            
            self.assertEqual(reporter.storage_file, self.storage_file)
            mock_sim.assert_called_once_with(self.storage_file)
            mock_gen.assert_called_once_with(self.storage_file)

    def test_run_stress_reporting_logic(self):
        sim_data = {uuid.uuid4().hex: random.randint(100, 500)}
        report_data = {uuid.uuid4().hex: ''.join(random.choices(string.ascii_lowercase, k=10))}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = sim_data

            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.return_value = report_data

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            mock_gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], report_data)

    def test_simulate_single_success(self):
        expected_result = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = expected_result

            reporter = StressReporter(self.storage_file)
            res = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(res, expected_result)

    def test_simulate_single_key_error(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError

            reporter = StressReporter(self.storage_file)
            res = reporter.simulate_single(self.symbol, self.percentage)

            self.assertEqual(res, {})

    def test_get_stream_data(self):
        raw_dump = [uuid.uuid4().hex, random.randint(1, 100)]

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator'), \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen_cls:
            
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = raw_dump

            reporter = StressReporter(self.storage_file)
            data = reporter.get_stream_data()

            mock_gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(data, raw_dump)

    def test_portfolio_stress_reporter_inheritance_and_pipeline(self):
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.StressReporter.run_stress_reporting') as mock_super_run:
            mock_super_run.return_value = expected_output

            pipeline_reporter = PortfolioStressReporter(self.storage_file)
            res = pipeline_reporter.run_stress_report(self.symbol, self.shifts)

            mock_super_run.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(res, expected_output)

    def test_generate_stress_report_helper(self):
        mock_result = {uuid.uuid4().hex: random.choice([True, False])}

        with patch('skills.market_portfolio_stress_reporter.StressReporter.run_stress_reporting') as mock_run:
            mock_run.return_value = mock_result

            res = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_run.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(res, mock_result)

    def test_run_stress_reporting_pipeline_helper(self):
        mock_result = {uuid.uuid4().hex: ''.join(random.choices(string.ascii_letters, k=8))}

        with patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter.run_stress_report') as mock_report:
            mock_report.return_value = mock_result

            res = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_report.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(res, mock_result)


if __name__ == '__main__':
    unittest.main()