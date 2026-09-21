import os
import unittest
import uuid
import random
from skills.market_portfolio_predictive_aggregator import PredictiveAggregator, aggregate_market_forecast
from skills.market_portfolio_collector_agent import MarketParser
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator

class TestPredictiveAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = uuid.uuid4().hex[:8]
        self.storage_file = f"test_storage_{self.unique_id}.json"
        self.symbol = f"SYM_{self.unique_id}"
        self.url = f"http://example.com/market/{self.unique_id}"
        self.shift = round(random.uniform(-50.0, 50.0), 2)
        self.initial_price = round(random.uniform(10.0, 1000.0), 2)

        parser = MarketParser(self.storage_file)
        if hasattr(parser, "fetch_and_store"):
            parser.fetch_and_store(self.symbol, self.initial_price)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_integration_build_advanced_forecast(self):
        aggregator = PredictiveAggregator(self.storage_file)
        result = aggregator.build_advanced_forecast(self.symbol, self.url, self.shift)

        self.assertIsInstance(result, dict)
        self.assertIn("valuation", result)
        self.assertIn("simulation", result)

        simulation = result["simulation"]
        self.assertEqual(simulation.get("symbol"), self.symbol)
        self.assertEqual(simulation.get("shift"), self.shift)
        self.assertIsInstance(simulation.get("projected_value"), (int, float))

    def test_integration_build_predictive_forecast(self):
        aggregator = PredictiveAggregator(self.storage_file)
        result = aggregator.build_predictive_forecast(self.symbol, self.url, self.shift)

        self.assertIsInstance(result, dict)
        self.assertIn("valuation", result)
        self.assertIn("simulation", result)

    def test_integration_aggregate_market_forecast_function(self):
        result = aggregate_market_forecast(self.storage_file, self.symbol, self.url, self.shift)

        self.assertIsInstance(result, dict)
        self.assertIn("valuation", result)
        self.assertIn("simulation", result)
        self.assertEqual(result["simulation"].get("symbol"), self.symbol)

if __name__ == "__main__":
    unittest.main()