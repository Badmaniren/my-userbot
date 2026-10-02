import unittest
from unittest.mock import patch
import uuid
import random
import string
import io

from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline
)


class TestMarketPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.shifts = [random.uniform(-0.5, 0.5) for _ in range(3)]
        self.percentage = random.uniform(-0.2, 0.2)

    def test_stress_reporter_run_stress_reporting(self):
        sim_result_key = uuid.uuid4().hex
        sim_result_val = random.randint(100, 1000)
        sim_data = {sim_result_key: sim_result_val}
        
        base_report_key = uuid.uuid4().hex
        base_report_val = uuid.uuid4().hex
        base_report_data = {base_report_key: base_report_val}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test', return_value=sim_data) as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report', return_value=base_report_data) as mock_gen:
            
            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim.assert_called_once_with(self.symbol, self.shifts)
            mock_gen.assert_called_once_with(self.symbol)

            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], base_report_data)
            self.assertIn(self.symbol, result["compact_text_report"])
            self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
            self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)
            self.assertEqual(result["tabular_report"][0]["results"], sim_data)
            self.assertEqual(result["chart_export"]["type"], "line")
            self.assertEqual(result["chart_export"]["data"], sim_data)

    def test_stress_reporter_simulate_single_success(self):
        expected_output = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.simulate_scenario', return_value=expected_output) as mock_sim:
            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_output)

    def test_stress_reporter_simulate_single_key_error(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.simulate_scenario', side_effect=KeyError) as mock_sim:
            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_stress_reporter_get_stream_data(self):
        stream_data_bytes = uuid.uuid4().bytes
        
        with patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.get_raw_stream_dump', return_value=stream_data_bytes) as mock_stream:
            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            mock_stream.assert_called_once()
            self.assertEqual(result, stream_data_bytes)

    def test_portfolio_stress_reporter_inheritance(self):
        sim_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        base_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test', return_value=sim_data), \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report', return_value=base_data):
            
            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], base_data)

    def test_generate_stress_report_function(self):
        sim_data = {uuid.uuid4().hex: random.randint(1, 100)}
        base_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test', return_value=sim_data) as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report', return_value=base_data):
            
            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_sim.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["tabular_report"][0]["shifts"], [self.percentage])

    def test_run_stress_reporting_pipeline_function(self):
        sim_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        base_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator.run_stress_test', return_value=sim_data) as mock_sim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator.generate_symbol_report', return_value=base_data):
            
            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_sim.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], base_data)


if __name__ == '__main__':
    unittest.main()