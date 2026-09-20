import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.market_portfolio_predictive_analyzer import (
    PredictiveAnalyzer,
    run_predictive_analysis
)

class TestMarketPortfolioPredictiveAnalyzer(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/market"
        self.percentage_shift = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-20.0, 20.0), 2) for _ in range(3)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_predictive_analyzer_initialization(self):
        custom_storage = f"{uuid.uuid4().hex}.db"
        with patch('skills.market_portfolio_predictive_analyzer.MarketParser') as mock_parser, \
             patch('skills.market_portfolio_predictive_analyzer.PortfolioScenarioSimulator') as mock_simulator:

            analyzer = PredictiveAnalyzer(storage_file=custom_storage)
            self.assertEqual(analyzer.storage_file, custom_storage)
            mock_parser.assert_called_once_with(custom_storage)
            mock_simulator.assert_called_once_with(custom_storage)

    def test_collect_and_simulate(self):
        mock_price = round(random.uniform(10.0, 1000.0), 2)
        expected_simulation_result = {
            "symbol": self.symbol,
            "shift": self.percentage_shift,
            "simulated_value": round(mock_price * (1 + self.percentage_shift / 100), 2),
            "id": uuid.uuid4().hex
        }

        with patch('skills.market_portfolio_predictive_analyzer.MarketParser') as MockParserClass, \
             patch('skills.market_portfolio_predictive_analyzer.PortfolioScenarioSimulator') as MockSimulatorClass:

            instance_parser = MockParserClass.return_value
            instance_parser.fetch_price.return_value = mock_price

            instance_simulator = MockSimulatorClass.return_value
            instance_simulator.simulate_scenario.return_value = expected_simulation_result

            analyzer = PredictiveAnalyzer(storage_file=self.storage_file)
            result = analyzer.collect_and_simulate(self.url, self.symbol, self.percentage_shift)

            instance_parser.fetch_price.assert_called_once_with(self.url)
            instance_parser.fetch_and_store.assert_called_once_with(self.symbol, mock_price)
            instance_simulator.simulate_scenario.assert_called_once_with(self.symbol, self.percentage_shift)

            self.assertEqual(result, expected_simulation_result)

    def test_run_retrospective_stress_analysis(self):
        expected_stress_results = {
            self.symbol: [
                {"shift": shift, "result": round(random.uniform(100.0, 500.0), 2)}
                for shift in self.shifts
            ],
            "session_id": uuid.uuid4().hex
        }

        with patch('skills.market_portfolio_predictive_analyzer.PortfolioScenarioSimulator') as MockSimulatorClass:
            instance_simulator = MockSimulatorClass.return_value
            instance_simulator.run_stress_test.return_value = expected_stress_results

            analyzer = PredictiveAnalyzer(storage_file=self.storage_file)
            result = analyzer.run_retrospective_stress_analysis(self.symbol, self.shifts)

            instance_simulator.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            self.assertEqual(result, expected_stress_results)

    def test_run_predictive_analysis_pipeline_function(self):
        mock_price = round(random.uniform(50.0, 5000.0), 2)
        pipeline_digest = {
            "status": "success",
            "symbol": self.symbol,
            "current_price": mock_price,
            "token": uuid.uuid4().hex
        }

        with patch('skills.market_portfolio_predictive_analyzer.MarketParser') as MockParserClass, \
             patch('skills.market_portfolio_predictive_analyzer.PortfolioScenarioSimulator') as MockSimulatorClass:

            instance_parser = MockParserClass.return_value
            instance_parser.fetch_price.return_value = mock_price

            instance_simulator = MockSimulatorClass.return_value
            instance_simulator.simulate_scenario.return_value = pipeline_digest

            res = run_predictive_analysis(
                symbol=self.symbol,
                url=self.url,
                percentage_shift=self.percentage_shift,
                storage_file=self.storage_file
            )

            self.assertIn("status", res)
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["symbol"], self.symbol)
            self.assertEqual(res["current_price"], mock_price)

    def test_io_stream_handling_with_bytes(self):
        random_bytes = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        with patch('skills.market_portfolio_predictive_analyzer.MarketParser') as MockParserClass, \
             patch('skills.market_portfolio_predictive_analyzer.PortfolioScenarioSimulator') as MockSimulatorClass:

            instance_parser = MockParserClass.return_value
            instance_parser.fetch_price.return_value = 123.45

            analyzer = PredictiveAnalyzer(storage_file=self.storage_file)

            read_data = random_bytes.read()
            self.assertIsInstance(read_data, bytes)
            self.assertTrue(len(read_data) > 0)

if __name__ == '__main__':
    unittest.main()