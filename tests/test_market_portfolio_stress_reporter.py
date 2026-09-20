import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_stress_reporter import (
    StressReporter,
    generate_stress_report
)

class TestMarketPortfolioStressReporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        self.shifts = [random.uniform(-0.5, 0.5), random.uniform(-0.2, 0.2)]
        self.percentage = random.uniform(-30.0, 30.0)

    def test_stress_reporter_initialization(self):
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as mock_simulator, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as mock_generator:
            
            reporter = StressReporter(self.storage_file)
            
            mock_simulator.assert_called_once_with(self.storage_file)
            mock_generator.assert_called_once_with(self.storage_file)
            self.assertEqual(reporter.storage_file, self.storage_file)

    def test_run_stress_reporting(self):
        mock_sim_result = {
            self.symbol: [
                {"shift": self.shifts[0], "simulated_price": random.uniform(10.0, 100.0)},
                {"shift": self.shifts[1], "simulated_price": random.uniform(10.0, 100.0)}
            ]
        }
        mock_report_data = f"Report-{uuid.uuid4().hex}"

        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSimulator, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGenerator:
            
            instance_sim = MockSimulator.return_value
            instance_sim.run_stress_test.return_value = mock_sim_result

            instance_gen = MockGenerator.return_value
            instance_gen.generate_symbol_report.return_value = mock_report_data

            reporter = StressReporter(self.storage_file)
            result = reporter.run_stress_reporting(self.symbol, self.shifts)

            instance_sim.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            instance_gen.generate_symbol_report.assert_called_once_with(self.symbol)

            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertEqual(result["simulation_results"], mock_sim_result)
            self.assertEqual(result["base_report"], mock_report_data)

    def test_generate_stress_report_wrapper(self):
        mock_output = {
            "status": "success",
            "token_dump": uuid.uuid4().hex
        }

        with patch('skills.market_portfolio_stress_reporter.StressReporter') as MockReporter:
            instance = MockReporter.return_value
            instance.run_stress_reporting.return_value = mock_output

            res = generate_stress_report(self.storage_file, self.symbol, self.percentage)

            MockReporter.assert_called_once_with(self.storage_file)
            instance.run_stress_reporting.assert_called_once()
            self.assertEqual(res, mock_output)

    def test_stress_reporter_with_io_stream(self):
        dummy_stream_content = f"stream-data-{uuid.uuid4().hex}".encode('utf-8')
        
        with patch('skills.market_portfolio_stress_reporter.PortfolioScenarioSimulator') as MockSimulator, \
             patch('skills.market_portfolio_stress_reporter.MarketReportGenerator') as MockGenerator:
            
            instance_sim = MockSimulator.return_value
            instance_sim.simulate_scenario.return_value = {"price": random.randint(100, 500)}

            instance_gen = MockGenerator.return_value
            instance_gen.get_raw_stream_dump.return_value = io.BytesIO(dummy_stream_content)

            reporter = StressReporter(self.storage_file)
            sim_res = reporter.simulate_single(self.symbol, self.percentage)
            stream_res = reporter.get_stream_data()

            self.assertEqual(stream_res.read(), dummy_stream_content)
            self.assertIn("price", sim_res)

if __name__ == '__main__':
    unittest.main()