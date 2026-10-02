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


class TestPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.shifts = [round(random.uniform(-0.5, 0.5), 2) for _ in range(3)]
        self.percentage = round(random.uniform(-0.2, 0.2), 2)

    def test_run_stress_reporting_success(self):
        sim_result_data = {uuid.uuid4().hex: random.randint(100, 1000)}
        base_report_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            instance_sim = MockSim.return_value
            instance_sim.run_stress_test.return_value = sim_result_data

            instance_gen = MockGen.return_value
            instance_gen.generate_symbol_report.return_value = base_report_data

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertIn("compact_text_report", result)
            self.assertIn("tabular_report", result)
            self.assertIn("chart_export", result)

            self.assertEqual(result["simulation_results"], sim_result_data)
            self.assertEqual(result["base_report"], base_report_data)
            self.assertIn(self.symbol, result["compact_text_report"])
            self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
            self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)
            self.assertEqual(result["chart_export"]["data"], sim_result_data)

    def test_simulate_single_success(self):
        expected_simulation = {uuid.uuid4().hex: random.random()}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim:
            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.return_value = expected_simulation

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            self.assertEqual(result, expected_simulation)
            instance_sim.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)

    def test_simulate_single_key_error(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim:
            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.side_effect = KeyError

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            self.assertEqual(result, {})

    def test_get_stream_data(self):
        stream_dump = [uuid.uuid4().hex for _ in range(3)]

        with patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            instance_gen = MockGen.return_value
            instance_gen.get_raw_stream_dump.return_value = stream_dump

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            self.assertEqual(result, stream_dump)

    def test_portfolio_stress_reporter_inheritance(self):
        sim_result_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        base_report_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            MockSim.return_value.run_stress_test.return_value = sim_result_data
            MockGen.return_value.generate_symbol_report.return_value = base_report_data

            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            self.assertEqual(result["simulation_results"], sim_result_data)
            self.assertEqual(result["base_report"], base_report_data)

    def test_generate_stress_report_functional(self):
        sim_result_data = {uuid.uuid4().hex: random.randint(1, 50)}
        base_report_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            MockSim.return_value.run_stress_test.return_value = sim_result_data
            MockGen.return_value.generate_symbol_report.return_value = base_report_data

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            self.assertEqual(result["simulation_results"], sim_result_data)
            self.assertEqual(result["tabular_report"][0]["shifts"], [self.percentage])

    def test_run_stress_reporting_pipeline_functional(self):
        sim_result_data = {uuid.uuid4().hex: random.uniform(10.0, 100.0)}
        base_report_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSim, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGen:
            
            MockSim.return_value.run_stress_test.return_value = sim_result_data
            MockGen.return_value.generate_symbol_report.return_value = base_report_data

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            self.assertEqual(result["simulation_results"], sim_result_data)
            self.assertEqual(result["base_report"], base_report_data)
            self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)


if __name__ == '__main__':
    unittest.main()