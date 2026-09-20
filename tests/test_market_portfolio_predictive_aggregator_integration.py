import os
import unittest
import uuid
import random
import tempfile

from skills.market_portfolio_predictive_aggregator import MarketPortfolioPredictiveAggregator
from skills.market_portfolio_collector_agent import PortfolioValuation as CollectorValuation
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator as ScenarioSimulator

class TestMarketPortfolioPredictiveAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"test_storage_{uuid.uuid4().hex}.json")
        
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex[:6]}"
        self.percentage_shift = round(random.uniform(-20.0, 20.0), 2)
        
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{}")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_predictive_aggregator_integration(self):
        collector_inst = CollectorValuation(self.storage_file)
        self.assertIsNotNone(collector_inst)

        simulator_inst = ScenarioSimulator(self.storage_file)
        self.assertIsNotNone(simulator_inst)

        aggregator = MarketPortfolioPredictiveAggregator(self.storage_file)
        self.assertIsNotNone(aggregator)

        self.assertTrue(hasattr(aggregator, "build_predictive_forecast"))
        
        forecast_result = aggregator.build_predictive_forecast(self.symbol, self.url, self.percentage_shift)
        
        self.assertIsInstance(forecast_result, dict)
        self.assertTrue(os.path.exists(self.storage_file))

if __name__ == "__main__":
    unittest.main()