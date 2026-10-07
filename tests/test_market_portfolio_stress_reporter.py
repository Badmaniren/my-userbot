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
        self.shifts = [random.uniform(-0.5, 0.5) for _ in range(random.randint(1, 3))]
        self.percentage = random.uniform(-0.2, 0.2)
        self.sim_result_data = {uuid.uuid4().hex: random.random()}
        self.base_report_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.stream_dump_data = [uuid.uuid4().hex for _ in range(3)]

    def test_run_stress_reporting(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = self.sim_result_data

            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.return_value = self.base_report_data

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            mock_gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertEqual(result["simulation_results"], self.sim_result_data)
            self.assertEqual(result["base_report"], self.base_report_data)
            self.assertIn(self.symbol, result["compact_text_report"])
            self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
            self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)
            self.assertEqual(result["tabular_report"][0]["results"], self.sim_result_data)
            self.assertEqual(result["chart_export"]["data"], self.sim_result_data)

    def test_simulate_single_success(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator"):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = self.sim_result_data

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, self.sim_result_data)

    def test_simulate_single_key_error(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator"):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_get_stream_data(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator"), \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = self.stream_dump_data

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            mock_gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(result, self.stream_dump_data)


class TestPortfolioStressReporter(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.shifts = [random.uniform(-1.0, 1.0)]

    def test_portfolio_stress_reporter_inheritance(self):
        with patch("skills.market_portfolio_stress_reporter.StressReporter.run_stress_reporting") as mock_super_run:
            expected_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_super_run.return_value = expected_payload

            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            mock_super_run.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, expected_payload)


class TestFunctionalHelpers(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=6))
        self.percentage = random.uniform(-0.5, 0.5)
        self.shifts = [self.percentage]
        self.expected_output = {uuid.uuid4().hex: random.randint(1, 100)}

    def test_generate_stress_report_helper(self):
        with patch("skills.market_portfolio_stress_reporter.StressReporter") as mock_reporter_cls:
            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.run_stress_reporting.return_value = self.expected_output

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_reporter_cls.assert_called_once_with(self.storage_file)
            mock_reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, self.expected_output)

    def test_run_stress_reporting_pipeline_helper(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioStressReporter") as mock_reporter_cls:
            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.run_stress_report.return_value = self.expected_output

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_reporter_cls.assert_called_once_with(self.storage_file)
            mock_reporter_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, self.expected_output)


if __name__ == "__main__":
    unittest.main()