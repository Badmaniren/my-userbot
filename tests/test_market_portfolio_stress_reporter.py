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
        self.shifts = [random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)]
        self.percentage = random.uniform(-0.2, 0.2)

    def test_run_stress_reporting_success(self):
        sim_result_data = {f"shift_{uuid.uuid4().hex[:4]}": random.randint(100, 1000)}
        base_report_data = {"status": "ok", "id": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = sim_result_data

            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.return_value = base_report_data

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            mock_gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertEqual(result["simulation_results"], sim_result_data)
            self.assertEqual(result["base_report"], base_report_data)
            self.assertEqual(result["compact_text_report"], f"Stress Report for {self.symbol}: Shifts={self.shifts}")
            self.assertEqual(result["tabular_report"], [{"symbol": self.symbol, "shifts": self.shifts, "results": sim_result_data}])
            self.assertEqual(result["chart_export"], {"type": "line", "data": sim_result_data})

    def test_simulate_single_success(self):
        expected_simulation = {uuid.uuid4().hex: random.uniform(1.0, 100.0)}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls:
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = expected_simulation

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_simulation)

    def test_simulate_single_key_error(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls:
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError("Not found")

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, {})

    def test_get_stream_data(self):
        stream_dump = [uuid.uuid4().hex, random.randint(1, 500)]

        with patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = stream_dump

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            mock_gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(result, stream_dump)

    def test_portfolio_stress_reporter_inheritance(self):
        sim_result_data = {uuid.uuid4().hex: random.random()}
        base_report_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = sim_result_data

            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.return_value = base_report_data

            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result["simulation_results"], sim_result_data)
            self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)

    def test_generate_stress_report_functional(self):
        sim_result_data = {uuid.uuid4().hex: random.randint(1, 10)}
        base_report_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = sim_result_data

            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.return_value = base_report_data

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(result["simulation_results"], sim_result_data)

    def test_run_stress_reporting_pipeline_functional(self):
        sim_result_data = {uuid.uuid4().hex: random.random()}
        base_report_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = sim_result_data

            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.return_value = base_report_data

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result["simulation_results"], sim_result_data)


if __name__ == "__main__":
    unittest.main()