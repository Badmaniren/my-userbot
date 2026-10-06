import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline
)

class TestMarketPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [round(random.uniform(-0.5, 0.5), 2) for _ in range(random.randint(1, 3))]
        self.percentage = round(random.uniform(-0.2, 0.2), 2)
        self.sim_result_data = {uuid.uuid4().hex: random.randint(100, 1000)}
        self.base_report_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.stream_dump_data = [uuid.uuid4().hex, uuid.uuid4().hex]

    def test_stress_reporter_run_stress_reporting(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            instance_sim = MockSim.return_value
            instance_sim.run_stress_test.return_value = self.sim_result_data

            instance_gen = MockGen.return_value
            instance_gen.generate_symbol_report.return_value = self.base_report_data

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            instance_sim.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            instance_gen.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertEqual(result["simulation_results"], self.sim_result_data)
            self.assertEqual(result["base_report"], self.base_report_data)
            self.assertIn(self.symbol, result["compact_text_report"])
            self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
            self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)
            self.assertEqual(result["tabular_report"][0]["results"], self.sim_result_data)
            self.assertEqual(result["chart_export"]["type"], "line")
            self.assertEqual(result["chart_export"]["data"], self.sim_result_data)

    def test_stress_reporter_simulate_single_success(self):
        single_sim_result = {uuid.uuid4().hex: random.random()}
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):
            
            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.return_value = single_sim_result

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            instance_sim.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, single_sim_result)

    def test_stress_reporter_simulate_single_key_error(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator'):
            
            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.side_effect = KeyError("Missing symbol")

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            instance_sim.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_stress_reporter_get_stream_data(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator'), \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            instance_gen = MockGen.return_value
            instance_gen.get_raw_stream_dump.return_value = self.stream_dump_data

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            instance_gen.get_raw_stream_dump.assert_called_once()
            self.assertEqual(result, self.stream_dump_data)

    def test_portfolio_stress_reporter_inheritance(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            instance_sim = MockSim.return_value
            instance_sim.run_stress_test.return_value = self.sim_result_data

            instance_gen = MockGen.return_value
            instance_gen.generate_symbol_report.return_value = self.base_report_data

            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            self.assertEqual(result["simulation_results"], self.sim_result_data)
            self.assertEqual(result["base_report"], self.base_report_data)

    def test_generate_stress_report_function(self):
        with patch('skills.market_portfolio_stress_reporter.StressReporter') as MockReporterClass:
            mock_reporter_instance = MockReporterClass.return_value
            expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_reporter_instance.run_stress_reporting.return_value = expected_output

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            MockReporterClass.assert_called_once_with(self.storage_file)
            mock_reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(result, expected_output)

    def test_run_stress_reporting_pipeline_function(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioStressReporter') as MockReporterClass:
            mock_reporter_instance = MockReporterClass.return_value
            expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_reporter_instance.run_stress_report.return_value = expected_output

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            MockReporterClass.assert_called_once_with(self.storage_file)
            mock_reporter_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, expected_output)

    def test_stream_data_binary_io_integration(self):
        random_bytes = uuid.uuid4().bytes
        stream_mock = io.BytesIO(random_bytes)

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator'), \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            instance_gen = MockGen.return_value
            instance_gen.get_raw_stream_dump.return_value = stream_mock.read()

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            self.assertEqual(result, random_bytes)


if __name__ == '__main__':
    unittest.main()