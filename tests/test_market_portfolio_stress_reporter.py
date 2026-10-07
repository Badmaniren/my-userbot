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
        self.percentage = round(random.uniform(-0.2, 0.2), 2)

    def test_stress_reporter_initialization(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen:
            
            reporter = StressReporter(self.storage_file)
            
            self.assertEqual(reporter.storage_file, self.storage_file)
            mock_sim.assert_called_once_with(self.storage_file)
            mock_gen.assert_called_once_with(self.storage_file)

    def test_run_stress_reporting_logic(self):
        sim_data = {f"shift_{uuid.uuid4().hex[:4]}": random.randint(100, 1000)}
        report_data = {f"metric_{uuid.uuid4().hex[:4]}": random.random()}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_class, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_class:
            
            mock_sim_instance = mock_sim_class.return_value
            mock_sim_instance.run_stress_test.return_value = sim_data

            mock_gen_instance = mock_gen_class.return_value
            mock_gen_instance.generate_symbol_report.return_value = report_data

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            mock_gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertEqual(result["simulation_results"], sim_data)
            self.assertEqual(result["base_report"], report_data)
            self.assertEqual(result["compact_text_report"], f"Stress Report for {self.symbol}: Shifts={self.shifts}")
            self.assertEqual(result["tabular_report"], [{"symbol": self.symbol, "shifts": self.shifts, "results": sim_data}])
            self.assertEqual(result["chart_export"], {"type": "line", "data": sim_data})

    def test_simulate_single_delegation(self):
        expected_output = {uuid.uuid4().hex: random.randint(10, 500)}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_class, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator"):
            
            mock_sim_instance = mock_sim_class.return_value
            mock_sim_instance.simulate_scenario.return_value = expected_output

            reporter = StressReporter(self.storage_file)
            res = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(res, expected_output)

    def test_get_stream_data_delegation(self):
        stream_dump = [uuid.uuid4().hex for _ in range(3)]

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator"), \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_class:
            
            mock_gen_instance = mock_gen_class.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = stream_dump

            reporter = StressReporter(self.storage_file)
            res = reporter.get_stream_data()

            mock_gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(res, stream_dump)

    def test_portfolio_stress_reporter_inheritance(self):
        sim_data = {uuid.uuid4().hex: random.random()}
        
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_class, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_class:
            
            mock_sim_instance = mock_sim_class.return_value
            mock_sim_instance.run_stress_test.return_value = sim_data
            mock_gen_class.return_value.generate_symbol_report.return_value = {}

            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            self.assertEqual(result["simulation_results"], sim_data)

    def test_generate_stress_report_functional(self):
        sim_data = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch("skills.market_portfolio_stress_reporter.StressReporter") as mock_reporter_class:
            mock_reporter_instance = mock_reporter_class.return_value
            expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_reporter_instance.run_stress_reporting.return_value = expected_dict

            res = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_reporter_class.assert_called_once_with(self.storage_file)
            mock_reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(res, expected_dict)

    def test_run_stress_reporting_pipeline_functional(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioStressReporter") as mock_pipeline_class:
            mock_pipeline_instance = mock_pipeline_class.return_value
            expected_result = {uuid.uuid4().hex: random.random()}
            mock_pipeline_instance.run_stress_report.return_value = expected_result

            res = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_pipeline_class.assert_called_once_with(self.storage_file)
            mock_pipeline_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(res, expected_result)


if __name__ == "__main__":
    unittest.main()