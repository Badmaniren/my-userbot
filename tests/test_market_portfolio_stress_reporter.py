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
        self.shifts = [random.uniform(-0.5, 0.5) for _ in range(random.randint(2, 5))]
        self.percentage = random.uniform(-0.2, 0.2)
        self.sim_results = {f"shift_{uuid.uuid4().hex[:4]}": random.uniform(-1000, 1000) for _ in range(3)}
        self.base_report_data = {"base_metric": random.randint(100, 500)}
        self.stream_dump = [uuid.uuid4().hex for _ in range(3)]

    def test_stress_reporter_initialization(self):
        reporter = StressReporter(self.storage_file)
        self.assertEqual(reporter.storage_file, self.storage_file)
        self.assertIsNotNone(reporter.simulator)
        self.assertIsNotNone(reporter.generator)

    def test_run_stress_reporting_logic(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            mock_sim_instance = MockSim.return_value
            mock_sim_instance.run_stress_test.return_value = self.sim_results

            mock_gen_instance = MockGen.return_value
            mock_gen_instance.generate_symbol_report.return_value = self.base_report_data

            reporter = StressReporter(self.storage_file)
            report = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            mock_gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertEqual(report["simulation_results"], self.sim_results)
            self.assertEqual(report["base_report"], self.base_report_data)
            self.assertIn(self.symbol, report["compact_text_report"])
            self.assertEqual(report["tabular_report"][0]["symbol"], self.symbol)
            self.assertEqual(report["tabular_report"][0]["shifts"], self.shifts)
            self.assertEqual(report["tabular_report"][0]["results"], self.sim_results)
            self.assertEqual(report["chart_export"]["type"], "line")
            self.assertEqual(report["chart_export"]["data"], self.sim_results)

    def test_simulate_single_success(self):
        expected_output = {"scenario_id": uuid.uuid4().hex, "impact": random.uniform(-50, 50)}
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim:
            mock_sim_instance = MockSim.return_value
            mock_sim_instance.simulate_scenario.return_value = expected_output

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_output)

    def test_simulate_single_key_error(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim:
            mock_sim_instance = MockSim.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_get_stream_data(self):
        with patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            mock_gen_instance = MockGen.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = self.stream_dump

            reporter = StressReporter(self.storage_file)
            data = reporter.get_stream_data()

            mock_gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(data, self.stream_dump)

    def test_portfolio_stress_reporter_inheritance(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            mock_sim_instance = MockSim.return_value
            mock_sim_instance.run_stress_test.return_value = self.sim_results

            mock_gen_instance = MockGen.return_value
            mock_gen_instance.generate_symbol_report.return_value = self.base_report_data

            reporter = PortfolioStressReporter(self.storage_file)
            report = reporter.run_stress_report(self.symbol, self.shifts)

            self.assertEqual(report["simulation_results"], self.sim_results)

    def test_generate_stress_report_function(self):
        with patch('skills.market_portfolio_stress_reporter.StressReporter') as MockReporterClass:
            mock_reporter_instance = MockReporterClass.return_value
            expected_dict = {"generated": uuid.uuid4().hex}
            mock_reporter_instance.run_stress_reporting.return_value = expected_dict

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            MockReporterClass.assert_called_once_with(self.storage_file)
            mock_reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(result, expected_dict)

    def test_run_stress_reporting_pipeline_function(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter') as MockPipelineClass:
            mock_pipeline_instance = MockPipelineClass.return_value
            expected_dict = {"pipeline": uuid.uuid4().hex}
            mock_pipeline_instance.run_stress_report.return_value = expected_dict

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            MockPipelineClass.assert_called_once_with(self.storage_file)
            mock_pipeline_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, expected_dict)

if __name__ == '__main__':
    unittest.main()