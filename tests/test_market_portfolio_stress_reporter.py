import unittest
from unittest.mock import patch
import uuid
import random
from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline,
)


class TestPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)]
        self.percentage = random.uniform(-1.0, 1.0)

    def test_stress_reporter_run_stress_reporting(self):
        mock_sim_results = {f"shift_{uuid.uuid4().hex[:4]}": random.random()}
        mock_base_report = {f"metric_{uuid.uuid4().hex[:4]}": random.randint(100, 500)}
        
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = mock_sim_results
            
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.generate_symbol_report.return_value = mock_base_report

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            mock_gen_instance.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertEqual(result["simulation_results"], mock_sim_results)
            self.assertEqual(result["base_report"], mock_base_report)
            self.assertIn(self.symbol, result["compact_text_report"])
            self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
            self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)
            self.assertEqual(result["tabular_report"][0]["results"], mock_sim_results)
            self.assertEqual(result["chart_export"]["type"], "line")
            self.assertEqual(result["chart_export"]["data"], mock_sim_results)

    def test_stress_reporter_simulate_single_success(self):
        expected_simulation = {f"key_{uuid.uuid4().hex[:4]}": random.randint(1, 1000)}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator"):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = expected_simulation

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, expected_simulation)

    def test_stress_reporter_simulate_single_key_error(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator"):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError

            reporter = StressReporter(self.storage_file)
            result = reporter.simulate_single(self.symbol, self.percentage)

            self.assertEqual(result, {})

    def test_stress_reporter_get_stream_data(self):
        expected_stream = [f"stream_item_{uuid.uuid4().hex[:4]}" for _ in range(3)]

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator"), \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator") as mock_gen_cls:
            
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = expected_stream

            reporter = StressReporter(self.storage_file)
            result = reporter.get_stream_data()

            mock_gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(result, expected_stream)

    def test_portfolio_stress_reporter_inheritance(self):
        mock_output = {f"out_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator"):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = mock_output

            reporter = PortfolioStressReporter(self.storage_file)
            result = reporter.run_stress_report(self.symbol, self.shifts)

            self.assertEqual(result["simulation_results"], mock_output)

    def test_generate_stress_report_helper(self):
        mock_sim_data = {f"res_{uuid.uuid4().hex[:4]}": random.random()}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator"):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = mock_sim_data

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, [self.percentage])
            self.assertEqual(result["simulation_results"], mock_sim_data)

    def test_run_stress_reporting_pipeline_helper(self):
        mock_pipeline_data = {f"pipe_{uuid.uuid4().hex[:4]}": random.randint(10, 50)}

        with patch("skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_reporter.MarketReportGenerator"):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.run_stress_test.return_value = mock_pipeline_data

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result["simulation_results"], mock_pipeline_data)


if __name__ == "__main__":
    unittest.main()