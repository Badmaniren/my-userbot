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

    def test_run_stress_reporting_success(self):
        storage = uuid.uuid4().hex
        symbol = uuid.uuid4().hex
        shifts = [random.uniform(-50.0, 0.0), random.uniform(0.1, 50.0)]
        
        sim_mock_data = {uuid.uuid4().hex: random.random()}
        gen_mock_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            instance_sim = MockSim.return_value
            instance_sim.run_stress_test.return_value = sim_mock_data
            
            instance_gen = MockGen.return_value
            instance_gen.generate_symbol_report.return_value = gen_mock_data

            reporter = StressReporter(storage)
            result = reporter.run_stress_reporting(symbol, shifts)

            MockSim.assert_called_once_with(storage)
            MockGen.assert_called_once_with(storage)
            instance_sim.run_stress_test.assert_called_once_with(symbol, shifts)
            instance_gen.generate_symbol_report.assert_called_once_with(symbol)

            self.assertEqual(result["simulation_results"], sim_mock_data)
            self.assertEqual(result["base_report"], gen_mock_data)

    def test_simulate_single_success(self):
        storage = uuid.uuid4().hex
        symbol = uuid.uuid4().hex
        percentage = random.uniform(-20.0, 20.0)
        expected_result = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):
            
            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.return_value = expected_result

            reporter = StressReporter(storage)
            res = reporter.simulate_single(symbol, percentage)

            instance_sim.simulate_scenario.assert_called_once_with(symbol, percentage)
            self.assertEqual(res, expected_result)

    def test_simulate_single_key_error(self):
        storage = uuid.uuid4().hex
        symbol = uuid.uuid4().hex
        percentage = random.uniform(-20.0, 20.0)

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):
            
            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.side_effect = KeyError

            reporter = StressReporter(storage)
            res = reporter.simulate_single(symbol, percentage)

            self.assertEqual(res, {})

    def test_get_stream_data(self):
        storage = uuid.uuid4().hex
        expected_stream = [uuid.uuid4().hex, uuid.uuid4().hex]

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator'), \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            instance_gen = MockGen.return_value
            instance_gen.get_raw_stream_dump.return_value = expected_stream

            reporter = StressReporter(storage)
            res = reporter.get_stream_data()

            instance_gen.get_raw_stream_dump.assert_called_once()
            self.assertEqual(res, expected_stream)

    def test_portfolio_stress_reporter_inheritance(self):
        storage = uuid.uuid4().hex
        symbol = uuid.uuid4().hex
        shifts = [random.uniform(-10.0, 10.0)]
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator'), \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'), \
             patch.object(StressReporter, 'run_stress_reporting', return_value=expected_output) as mock_run:
            
            reporter = PortfolioStressReporter(storage)
            res = reporter.run_stress_report(symbol, shifts)

            mock_run.assert_called_once_with(symbol, shifts)
            self.assertEqual(res, expected_output)

    def test_generate_stress_report_function(self):
        storage = uuid.uuid4().hex
        symbol = uuid.uuid4().hex
        percentage = random.uniform(-5.0, 5.0)
        expected_output = {uuid.uuid4().hex: random.random()}

        with patch.object(StressReporter, 'run_stress_reporting', return_value=expected_output) as mock_run:
            res = generate_stress_report(storage, symbol, percentage)

            mock_run.assert_called_once_with(symbol, [percentage])
            self.assertEqual(res, expected_output)

    def test_run_stress_reporting_pipeline_function(self):
        storage = uuid.uuid4().hex
        symbol = uuid.uuid4().hex
        shifts = [random.uniform(-30.0, 30.0), random.uniform(-30.0, 30.0)]
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(PortfolioStressReporter, 'run_stress_report', return_value=expected_output) as mock_run:
            res = run_stress_reporting_pipeline(storage, symbol, shifts)

            mock_run.assert_called_once_with(symbol, shifts)
            self.assertEqual(res, expected_output)


if __name__ == '__main__':
    unittest.main()