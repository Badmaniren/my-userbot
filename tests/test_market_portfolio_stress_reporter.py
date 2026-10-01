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
        self.shifts = [round(random.uniform(-0.5, 0.5), 2) for _ in range(random.randint(1, 3))]
        self.percentage = round(random.uniform(-0.3, 0.3), 2)
        self.sim_data_key = uuid.uuid4().hex
        self.sim_data_val = random.randint(100, 9999)
        self.report_key = uuid.uuid4().hex
        self.report_val = uuid.uuid4().hex
        self.stream_data = [uuid.uuid4().hex for _ in range(3)]

    def test_run_stress_reporting(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            sim_instance = MockSim.return_value
            gen_instance = MockGen.return_value

            expected_sim_result = {self.sim_data_key: self.sim_data_val}
            expected_base_report = {self.report_key: self.report_val}

            sim_instance.run_stress_test.return_value = expected_sim_result
            gen_instance.generate_symbol_report.return_value = expected_base_report

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            MockSim.assert_called_once_with(self.storage_file)
            MockGen.assert_called_once_with(self.storage_file)
            sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertEqual(result["simulation_results"], expected_sim_result)
            self.assertEqual(result["base_report"], expected_base_report)

    def test_simulate_single_success(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):
            
            sim_instance = MockSim.return_value
            expected_output = {uuid.uuid4().hex: random.randint(1, 500)}
            sim_instance.simulate_scenario.return_value = expected_output

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_output)

    def test_simulate_single_key_error(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):
            
            sim_instance = MockSim.return_value
            sim_instance.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_get_stream_data(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator'), \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            gen_instance = MockGen.return_value
            gen_instance.get_raw_stream_dump.return_value = self.stream_data

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(result, self.stream_data)


class TestPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        self.shifts = [round(random.uniform(-1.0, 1.0), 2)]

    def test_portfolio_stress_report_inheritance(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            sim_instance = MockSim.return_value
            gen_instance = MockGen.return_value

            sim_res = {uuid.uuid4().hex: uuid.uuid4().hex}
            rep_res = {uuid.uuid4().hex: uuid.uuid4().hex}

            sim_instance.run_stress_test.return_value = sim_res
            gen_instance.generate_symbol_report.return_value = rep_res

            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            self.assertEqual(result["simulation_results"], sim_res)
            self.assertEqual(result["base_report"], rep_res)


class TestFunctionalHelpers(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=3))
        self.percentage = round(random.uniform(-0.5, 0.5), 2)

    def test_generate_stress_report_function(self):
        with patch('skills.market_portfolio_stress_reporter.StressReporter') as MockReporterClass:
            mock_reporter_instance = MockReporterClass.return_value
            expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_reporter_instance.run_stress_reporting.return_value = expected_dict

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            MockReporterClass.assert_called_once_with(self.storage_file)
            mock_reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(result, expected_dict)

    def test_run_stress_reporting_pipeline_function(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter') as MockPRClass:
            mock_pr_instance = MockPRClass.return_value
            expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_pr_instance.run_stress_report.return_value = expected_dict

            shifts_arg = [round(random.uniform(-0.2, 0.2), 2)]
            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, shifts_arg)

            MockPRClass.assert_called_once_with(self.storage_file)
            mock_pr_instance.run_stress_report.assert_called_once_with(self.symbol, shifts_arg)
            self.assertEqual(result, expected_dict)


if __name__ == '__main__':
    unittest.main()