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
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.db"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.shifts = [round(random.uniform(-0.5, 0.5), 4) for _ in range(random.randint(2, 5))]
        self.percentage = round(random.uniform(-0.3, 0.3), 4)

    def test_stress_reporter_run_stress_reporting(self):
        sim_data = {uuid.uuid4().hex: random.uniform(10.0, 1000.0) for _ in range(3)}
        report_data = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(2)}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as MockGen:

            instance_sim = MockSim.return_value
            instance_sim.run_stress_test.return_value = sim_data

            instance_gen = MockGen.return_value
            instance_gen.generate_symbol_report.return_value = report_data

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            instance_sim.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            instance_gen.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], report_data)

    def test_stress_reporter_simulate_single_success(self):
        expected_output = {uuid.uuid4().hex: random.random()}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator"):

            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.return_value = expected_output

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            instance_sim.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_output)

    def test_stress_reporter_simulate_single_key_error(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator"):

            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            instance_sim.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_stress_reporter_get_stream_data(self):
        stream_dump = [uuid.uuid4().hex for _ in range(random.randint(3, 6))]

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator"), \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as MockGen:

            instance_gen = MockGen.return_value
            instance_gen.get_raw_stream_dump.return_value = stream_dump

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            instance_gen.get_raw_stream_dump.assert_called_once()
            self.assertEqual(result, stream_dump)

    def test_portfolio_stress_reporter_inheritance(self):
        sim_data = {uuid.uuid4().hex: random.randint(1, 100)}
        report_data = {uuid.uuid4().hex: random.randint(100, 200)}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as MockGen:

            instance_sim = MockSim.return_value
            instance_sim.run_stress_test.return_value = sim_data

            instance_gen = MockGen.return_value
            instance_gen.generate_symbol_report.return_value = report_data

            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            instance_sim.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            instance_gen.generate_symbol_report.assert_called_once_with(self.symbol)
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], report_data)

    def test_generate_stress_report_function(self):
        sim_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        report_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as MockGen:

            instance_sim = MockSim.return_value
            instance_sim.run_stress_test.return_value = sim_data

            instance_gen = MockGen.return_value
            instance_gen.generate_symbol_report.return_value = report_data

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            instance_sim.run_stress_test.assert_called_once_with(self.symbol, [self.percentage])
            instance_gen.generate_symbol_report.assert_called_once_with(self.symbol)
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], report_data)

    def test_run_stress_reporting_pipeline_function(self):
        sim_data = {uuid.uuid4().hex: random.random()}
        report_data = {uuid.uuid4().hex: random.random()}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as MockGen:

            instance_sim = MockSim.return_value
            instance_sim.run_stress_test.return_value = sim_data

            instance_gen = MockGen.return_value
            instance_gen.generate_symbol_report.return_value = report_data

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            instance_sim.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            instance_gen.generate_symbol_report.assert_called_once_with(self.symbol)
            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], report_data)


if __name__ == "__main__":
    unittest.main()