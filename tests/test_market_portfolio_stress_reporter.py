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
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.shifts = [random.uniform(-0.5, 0.5) for _ in range(random.randint(1, 3))]
        self.percentage = random.uniform(-0.3, 0.3)

    def test_run_stress_reporting(self):
        sim_result_mock = {uuid.uuid4().hex: random.random()}
        base_report_mock = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = sim_result_mock

            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.return_value = base_report_mock

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            mock_gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertEqual(result["simulation_results"], sim_result_mock)
            self.assertEqual(result["base_report"], base_report_mock)

    def test_simulate_single_success(self):
        expected_output = {uuid.uuid4().hex: random.randint(100, 500)}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls:
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = expected_output

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_output)

    def test_simulate_single_key_error(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls:
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_get_stream_data(self):
        stream_dump_mock = [uuid.uuid4().hex for _ in range(3)]

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator'), \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen_cls:
            
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = stream_dump_mock

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            mock_gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(result, stream_dump_mock)

    def test_portfolio_stress_reporter_inheritance(self):
        inherited_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(StressReporter, 'run_stress_reporting', return_value=inherited_result) as mock_super_run:
            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            mock_super_run.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, inherited_result)

    def test_generate_stress_report_functional(self):
        functional_result = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_stress_reporter.StressReporter') as mock_reporter_cls:
            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.run_stress_reporting.return_value = functional_result

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_reporter_cls.assert_called_once_with(self.storage_file)
            mock_reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(result, functional_result)

    def test_run_stress_reporting_pipeline_functional(self):
        pipeline_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter') as mock_reporter_cls:
            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.run_stress_report.return_value = pipeline_result

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_reporter_cls.assert_called_once_with(self.storage_file)
            mock_reporter_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, pipeline_result)


if __name__ == '__main__':
    unittest.main()