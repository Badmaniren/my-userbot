import unittest
from unittest.mock import patch
import uuid
import random
from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline
)

class TestStressReporter(unittest.TestCase):

    def test_stress_reporter_init_and_run(self):
        storage = f"{uuid.uuid4().hex}.db"
        symbol = uuid.uuid4().hex[:6].upper()
        shifts = [random.uniform(-50.0, 50.0), random.uniform(-50.0, 50.0)]
        
        sim_data = {uuid.uuid4().hex: random.random()}
        report_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = sim_data
            
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.return_value = report_data

            reporter = StressReporter(storage)
            result = reporter.run_stress_reporting(symbol, shifts)

            mock_sim_cls.assert_called_once_with(storage)
            mock_gen_cls.assert_called_once_with(storage)
            mock_sim_instance.run_stress_test.assert_called_once_with(symbol, shifts)
            mock_gen_instance.generate_symbol_report.assert_called_once_with(symbol)

            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], report_data)

    def test_stress_reporter_simulate_single(self):
        storage = uuid.uuid4().hex
        symbol = uuid.uuid4().hex[:5]
        percentage = random.uniform(-10.0, 10.0)
        expected_res = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_sim_cls, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = expected_res

            reporter = StressReporter(storage)
            res = reporter.simulate_single(symbol, percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(symbol, percentage)
            self.assertEqual(res, expected_res)

    def test_stress_reporter_get_stream_data(self):
        storage = uuid.uuid4().hex
        stream_dump = [uuid.uuid4().hex, uuid.uuid4().hex]

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator'), \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_gen_cls:
            
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = stream_dump

            reporter = StressReporter(storage)
            res = reporter.get_stream_data()

            mock_gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(res, stream_dump)

    def test_portfolio_stress_reporter_inheritance(self):
        storage = uuid.uuid4().hex
        symbol = uuid.uuid4().hex[:4]
        shifts = [random.randint(1, 5)]
        expected = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator'), \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'), \
             patch.object(StressReporter, 'run_stress_reporting', return_value=expected) as mock_super_run:
            
            reporter = PortfolioStressReporter(storage)
            res = reporter.run_stress_report(symbol, shifts)

            mock_super_run.assert_called_once_with(symbol, shifts)
            self.assertEqual(res, expected)

    def test_generate_stress_report_function(self):
        storage = uuid.uuid4().hex
        symbol = uuid.uuid4().hex[:5]
        percentage = random.uniform(1.0, 99.0)
        expected = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.StressReporter') as mock_reporter_cls:
            mock_instance = mock_reporter_cls.return_value
            mock_instance.run_stress_reporting.return_value = expected

            res = generate_stress_report(storage, symbol, percentage)

            mock_reporter_cls.assert_called_once_with(storage)
            mock_instance.run_stress_reporting.assert_called_once_with(symbol, [percentage])
            self.assertEqual(res, expected)

    def test_run_stress_reporting_pipeline_function(self):
        storage = uuid.uuid4().hex
        symbol = uuid.uuid4().hex[:4]
        shifts = [random.uniform(-10, 10), random.uniform(-10, 10)]
        expected = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter') as mock_reporter_cls:
            mock_instance = mock_reporter_cls.return_value
            mock_instance.run_stress_report.return_value = expected

            res = run_stress_reporting_pipeline(storage, symbol, shifts)

            mock_reporter_cls.assert_called_once_with(storage)
            mock_instance.run_stress_report.assert_called_once_with(symbol, shifts)
            self.assertEqual(res, expected)

if __name__ == '__main__':
    unittest.main()