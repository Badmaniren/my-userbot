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


class TestPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.shifts = [round(random.uniform(-0.5, 0.5), 4) for _ in range(random.randint(2, 5))]
        self.percentage = round(random.uniform(-0.2, 0.2), 4)
        
        self.sim_results_mock = {
            "var": random.randint(1000, 50000),
            "liquidity_drop": random.uniform(0.1, 0.9),
            "scenario": uuid.uuid4().hex
        }
        self.base_report_mock = {
            "symbol": self.symbol,
            "status": "OK",
            "metric": random.random()
        }
        self.raw_stream_mock = [random.randint(1, 100) for _ in range(3)]

    def test_stress_reporter_initialization(self):
        reporter = StressReporter(self.storage_file)
        self.assertEqual(reporter.storage_file, self.storage_file)
        self.assertIsNotNone(reporter.simulator)
        self.assertIsNotNone(reporter.generator)

    def test_run_stress_reporting(self):
        reporter = StressReporter(self.storage_file)
        
        with patch.object(reporter.simulator, 'run_stress_test', return_value=self.sim_results_mock) as mock_sim, \
             patch.object(reporter.generator, 'generate_symbol_report', return_value=self.base_report_mock) as mock_gen:
            
            res = reporter.run_stress_reporting(self.symbol, self.shifts)
            
            mock_sim.assert_called_once_with(self.symbol, self.shifts)
            mock_gen.assert_called_once_with(self.symbol)
            
            self.assertEqual(res["simulation_results"], self.sim_results_mock)
            self.assertEqual(res["base_report"], self.base_report_mock)
            self.assertIn(self.symbol, res["compact_text_report"])
            self.assertEqual(res["tabular_report"][0]["symbol"], self.symbol)
            self.assertEqual(res["tabular_report"][0]["shifts"], self.shifts)
            self.assertEqual(res["tabular_report"][0]["results"], self.sim_results_mock)
            self.assertEqual(res["chart_export"]["type"], "line")
            self.assertEqual(res["chart_export"]["data"], self.sim_results_mock)

    def test_simulate_single_success(self):
        reporter = StressReporter(self.storage_file)
        expected_output = {"scenario_result": random.randint(100, 500)}
        
        with patch.object(reporter.simulator, 'simulate_scenario', return_value=expected_output) as mock_sim:
            res = reporter.simulate_single(self.symbol, self.percentage)
            mock_sim.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(res, expected_output)

    def test_simulate_single_key_error(self):
        reporter = StressReporter(self.storage_file)
        
        with patch.object(reporter.simulator, 'simulate_scenario', side_effect=KeyError) as mock_sim:
            res = reporter.simulate_single(self.symbol, self.percentage)
            mock_sim.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(res, {})

    def test_get_stream_data(self):
        reporter = StressReporter(self.storage_file)
        
        with patch.object(reporter.generator, 'get_raw_stream_dump', return_value=self.raw_stream_mock) as mock_stream:
            res = reporter.get_stream_data()
            mock_stream.assert_called_once()
            self.assertEqual(res, self.raw_stream_mock)

    def test_portfolio_stress_reporter_inheritance(self):
        reporter = PortfolioStressReporter(self.storage_file)
        self.assertIsInstance(reporter, StressReporter)
        
        with patch.object(reporter, 'run_stress_reporting', return_value={"status": "passed"}) as mock_run:
            res = reporter.run_stress_report(self.symbol, self.shifts)
            mock_run.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(res, {"status": "passed"})

    def test_generate_stress_report_function(self):
        with patch('skills.market_portfolio_stress_reporter.StressReporter') as MockReporterClass:
            mock_instance = MockReporterClass.return_value
            expected_payload = {"key": uuid.uuid4().hex}
            mock_instance.run_stress_reporting.return_value = expected_payload
            
            res = generate_stress_report(self.storage_file, self.symbol, self.percentage)
            
            MockReporterClass.assert_called_once_with(self.storage_file)
            mock_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(res, expected_payload)

    def test_run_stress_reporting_pipeline_function(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter') as MockPipelineClass:
            mock_instance = MockPipelineClass.return_value
            expected_payload = {"pipeline_status": uuid.uuid4().hex}
            mock_instance.run_stress_report.return_value = expected_payload
            
            res = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
            
            MockPipelineClass.assert_called_once_with(self.storage_file)
            mock_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(res, expected_payload)


if __name__ == '__main__':
    unittest.main()