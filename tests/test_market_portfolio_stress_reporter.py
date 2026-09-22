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
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        self.shifts = [round(random.uniform(-0.2, 0.2), 2) for _ in range(random.randint(2, 5))]
        self.percentage = round(random.uniform(-0.1, 0.1), 2)
        
        self.mock_sim_result = {
            "".join(random.choices(string.ascii_lowercase, k=5)): random.randint(100, 1000)
            for _ in range(3)
        }
        self.mock_base_report = {
            "".join(random.choices(string.ascii_lowercase, k=5)): uuid.uuid4().hex
            for _ in range(3)
        }
        self.mock_stream_dump = [random.randint(1, 100) for _ in range(4)]

    def test_stress_reporter_init(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen:
            
            reporter = StressReporter(self.storage_file)
            
            self.assertEqual(reporter.storage_file, self.storage_file)
            mock_sim.assert_called_once_with(self.storage_file)
            mock_gen.assert_called_once_with(self.storage_file)

    def test_run_stress_reporting(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen_cls:
            
            sim_instance = mock_sim_cls.return_value
            sim_instance.run_stress_test.return_value = self.mock_sim_result

            gen_instance = mock_gen_cls.return_value
            gen_instance.generate_symbol_report.return_value = self.mock_base_report

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertEqual(result["simulation_results"], self.mock_sim_result)
            self.assertEqual(result["base_report"], self.mock_base_report)

    def test_simulate_single(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls:
            sim_instance = mock_sim_cls.return_value
            expected_output = {uuid.uuid4().hex: random.random()}
            sim_instance.simulate_scenario.return_value = expected_output

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_output)

    def test_get_stream_data(self):
        with patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen_cls:
            gen_instance = mock_gen_cls.return_value
            gen_instance.get_raw_stream_dump.return_value = self.mock_stream_dump

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(result, self.mock_stream_dump)

    def test_portfolio_stress_reporter_inheritance_and_execution(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen_cls:
            
            sim_instance = mock_sim_cls.return_value
            sim_instance.run_stress_test.return_value = self.mock_sim_result
            gen_instance = mock_gen_cls.return_value
            gen_instance.generate_symbol_report.return_value = self.mock_base_report

            reporter = PortfolioStressReporter(self.storage_file)
            self.assertIsInstance(reporter, StressReporter)

            result = reporter.run_stress_report(self.symbol, self.shifts)

            sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)
            self.assertEqual(result["simulation_results"], self.mock_sim_result)
            self.assertEqual(result["base_report"], self.mock_base_report)

    def test_generate_stress_report_helper(self):
        with patch('skills.market_portfolio_stress_reporter.StressReporter') as mock_reporter_cls:
            reporter_instance = mock_reporter_cls.return_value
            expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
            reporter_instance.run_stress_reporting.return_value = expected_dict

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_reporter_cls.assert_called_once_with(self.storage_file)
            reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(result, expected_dict)

    def test_run_stress_reporting_pipeline_helper(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter') as mock_reporter_cls:
            reporter_instance = mock_reporter_cls.return_value
            expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
            reporter_instance.run_stress_report.return_value = expected_dict

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_reporter_cls.assert_called_once_with(self.storage_file)
            reporter_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, expected_dict)


if __name__ == '__main__':
    unittest.main()