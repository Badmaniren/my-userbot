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
        self.shifts = [round(random.uniform(-0.5, 0.5), 2) for _ in range(random.randint(1, 3))]
        self.percentage = self.shifts[0]

    def test_run_stress_reporting_success(self):
        expected_sim_result = {
            self.symbol: {str(uuid.uuid4().hex): random.randint(100, 1000)}
        }
        expected_base_report = {
            "symbol": self.symbol,
            "status": ''.join(random.choices(string.ascii_lowercase, k=6))
        }

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = expected_sim_result

            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.return_value = expected_base_report

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            mock_gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertEqual(result["simulation_results"], expected_sim_result)
            self.assertEqual(result["base_report"], expected_base_report)

    def test_simulate_single_success(self):
        expected_simulation = {
            "shift": self.percentage,
            "value": random.randint(5000, 15000)
        }

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls:
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = expected_simulation

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_simulation)

    def test_simulate_single_key_error_handling(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls:
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError("Missing symbol")

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_get_stream_data(self):
        expected_stream = [
            {uuid.uuid4().hex: random.randint(1, 100)} for _ in range(3)
        ]

        with patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = expected_stream

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            mock_gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(result, expected_stream)

    def test_portfolio_stress_reporter_inheritance(self):
        expected_result = {
            "simulation_results": {uuid.uuid4().hex: random.random()},
            "base_report": {uuid.uuid4().hex: uuid.uuid4().hex}
        }

        with patch("skills.market_portfolio_stress_reporter.StressReporter.run_stress_reporting", return_value=expected_result) as mock_super_method:
            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            mock_super_method.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, expected_result)

    def test_generate_stress_report_functional(self):
        expected_result = {
            "simulation_results": {uuid.uuid4().hex: random.random()},
            "base_report": {uuid.uuid4().hex: random.random()}
        }

        with patch("skills.market_portfolio_stress_reporter.StressReporter.run_stress_reporting", return_value=expected_result) as mock_run:
            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_run.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(result, expected_result)

    def test_run_stress_reporting_pipeline_functional(self):
        expected_result = {
            "simulation_results": {uuid.uuid4().hex: random.random()},
            "base_report": {uuid.uuid4().hex: random.random()}
        }

        with patch("skills.market_portfolio_stress_reporter.PortfolioStressReporter.run_stress_report", return_value=expected_result) as mock_pipeline:
            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_pipeline.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()