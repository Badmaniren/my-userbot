import unittest
from unittest.mock import patch
import uuid
import random
from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline
)

class TestMarketPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [round(random.uniform(-50.0, 50.0), 2), round(random.uniform(-50.0, 50.0), 2)]
        self.percentage = round(random.uniform(-25.0, 25.0), 2)

        self.mock_sim_results = [
            {"shift_percentage": self.shifts[0], "resulting_valuation": round(random.uniform(100.0, 1000.0), 4)},
            {"shift_percentage": self.shifts[1], "resulting_valuation": round(random.uniform(100.0, 1000.0), 4)}
        ]
        self.mock_base_report = {
            "symbol": self.symbol,
            "status": uuid.uuid4().hex,
            "metrics": {"valuation": round(random.uniform(500.0, 1500.0), 4)}
        }
        self.mock_single_sim = {
            "shift_percentage": self.percentage,
            "resulting_valuation": round(random.uniform(200.0, 800.0), 4)
        }
        self.mock_stream_dump = [
            {"event": uuid.uuid4().hex, "value": random.randint(1, 100)}
        ]

    def test_stress_reporter_run_stress_reporting(self):
        reporter = StressReporter(self.storage_file)

        with patch.object(reporter.simulator, "run_stress_test", return_value=self.mock_sim_results) as mock_sim, \
             patch.object(reporter.generator, "generate_symbol_report", return_value=self.mock_base_report) as mock_gen:
            
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            mock_sim.assert_called_once_with(self.symbol, self.shifts)
            mock_gen.assert_called_once_with(self.symbol)

            self.assertIsInstance(result, dict)
            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertEqual(result["simulation_results"], self.mock_sim_results)
            self.assertEqual(result["base_report"], self.mock_base_report)
            self.assertIsInstance(result["simulation_results"], list)
            self.assertIsInstance(result["base_report"], dict)

    def test_stress_reporter_simulate_single(self):
        reporter = StressReporter(self.storage_file)

        with patch.object(reporter.simulator, "simulate_scenario", return_value=self.mock_single_sim) as mock_single:
            result = reporter.simulate_single(self.symbol, self.percentage)

            mock_single.assert_called_once_with(self.symbol, self.percentage)
            self.assertEqual(result, self.mock_single_sim)
            self.assertIsInstance(result, dict)
            self.assertEqual(result["shift_percentage"], self.percentage)

    def test_stress_reporter_get_stream_data(self):
        reporter = StressReporter(self.storage_file)
        
        with patch.object(reporter.generator, "get_raw_stream_dump", return_value=self.mock_stream_dump) as mock_stream:
            result = reporter.get_stream_data()
            
            mock_stream.assert_called_once()
            self.assertEqual(result, self.mock_stream_dump)
            self.assertIsInstance(result, list)

    def test_portfolio_stress_reporter_inheritance(self):
        reporter = PortfolioStressReporter(self.storage_file)
        self.assertIsInstance(reporter, StressReporter)

        with patch.object(reporter, "run_stress_reporting", return_value={"simulation_results": self.mock_sim_results, "base_report": self.mock_base_report}) as mock_reporting:
            result = reporter.run_stress_report(self.symbol, self.shifts)

            mock_reporting.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result["simulation_results"], self.mock_sim_results)

    def test_generate_stress_report_helper(self):
        with patch("skills.market_portfolio_stress_reporter.StressReporter") as MockReporterClass:
            mock_instance = MockReporterClass.return_value
            mock_instance.run_stress_reporting.return_value = {
                "simulation_results": self.mock_sim_results,
                "base_report": self.mock_base_report
            }

            result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            MockReporterClass.assert_called_once_with(self.storage_file)
            mock_instance.run_stress_reporting.assert_called_once_with(self.symbol, [self.percentage])
            self.assertIn("simulation_results", result)

    def test_run_stress_reporting_pipeline_helper(self):
        with patch("skills.market_portfolio_stress_reporter.PortfolioStressReporter") as MockPipelineClass:
            mock_instance = MockPipelineClass.return_value
            mock_instance.run_stress_report.return_value = {
                "simulation_results": self.mock_sim_results,
                "base_report": self.mock_base_report
            }

            result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

            MockPipelineClass.assert_called_once_with(self.storage_file)
            mock_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result["base_report"], self.mock_base_report)

if __name__ == "__main__":
    unittest.main()