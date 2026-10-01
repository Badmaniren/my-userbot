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
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.shifts = [round(random.uniform(-0.5, 0.5), 2) for _ in range(random.randint(1, 4))]
        self.percentage = round(random.uniform(-0.3, 0.3), 2)

    def test_run_stress_reporting_success(self):
        mock_sim_results = {str(uuid.uuid4().hex): random.randint(100, 1000)}
        mock_base_report = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_stream_data = [uuid.uuid4().hex for _ in range(3)]

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as MockGenerator:

            instance_sim = MockSimulator.return_value
            instance_sim.run_stress_test.return_value = mock_sim_results

            instance_gen = MockGenerator.return_value
            instance_gen.generate_symbol_report.return_value = mock_base_report
            instance_gen.get_raw_stream_dump.return_value = mock_stream_data

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            instance_sim.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            instance_gen.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertEqual(result["simulation_results"], mock_sim_results)
            self.assertEqual(result["base_report"], mock_base_report)
            self.assertIn(self.symbol, result["compact_text_report"])
            self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
            self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)
            self.assertEqual(result["tabular_report"][0]["results"], mock_sim_results)
            self.assertEqual(result["chart_export"]["data"], mock_sim_results)

    def test_simulate_single_success(self):
        mock_simulation_output = {uuid.uuid4().hex: random.random()}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as MockSimulator:
            instance_sim = MockSimulator.return_value
            instance_sim.simulate_scenario.return_value = mock_simulation_output

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            instance_sim.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, mock_simulation_output)

    def test_simulate_single_key_error(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as MockSimulator:
            instance_sim = MockSimulator.return_value
            instance_sim.simulate_scenario.side_effect = KeyError

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            instance_sim.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_get_stream_data(self):
        mock_stream_data = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as MockGenerator:
            instance_gen = MockGenerator.return_value
            instance_gen.get_raw_stream_dump.return_value = mock_stream_data

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            instance_gen.get_raw_stream_dump.assert_called_once()
            self.assertEqual(result, mock_stream_data)


class TestPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.shifts = [round(random.uniform(-0.2, 0.2), 2)]

    def test_run_stress_report_delegation(self):
        mock_expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_reporter.StressReporter.run_stress_reporting") as mock_run:
            mock_run.return_value = mock_expected_output

            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            mock_run.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, mock_expected_output)


class TestFunctionalHelpers(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=6))
        self.percentage = round(random.uniform(-0.5, 0.5), 2)

    def test_generate_stress_report_wrapper(self):
        mock_output = {uuid.uuid4().hex: random.randint(1, 500)}

        with patch("skills.market_portfolio_stress_reporter.StressReporter.run_stress_reporting") as mock_run:
            mock_run.return_value = mock_output

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_run.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(result, mock_output)

    def test_run_stress_reporting_pipeline_wrapper(self):
        mock_shifts = [round(random.uniform(-0.1, 0.1), 2) for _ in range(2)]
        mock_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_reporter.PortfolioStressReporter.run_stress_report") as mock_run:
            mock_run.return_value = mock_output

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, mock_shifts)

            mock_run.assert_called_once_with(self.symbol, mock_shifts)
            self.assertEqual(result, mock_output)


if __name__ == "__main__":
    unittest.main()