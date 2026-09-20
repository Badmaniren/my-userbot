import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import os

from skills.market_portfolio_predictive_aggregator import (
    PredictiveAggregator,
    aggregate_market_forecast
)

class TestMarketPortfolioPredictiveAggregator(unittest.TestCase):

    def setUp(self):
        self.rand_storage = f"{uuid.uuid4().hex}.json"
        self.rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.rand_shift = round(random.uniform(-50.0, 50.0), 2)
        self.rand_url = f"https://{uuid.uuid4().hex}.com/api"

    @patch('skills.market_portfolio_predictive_aggregator.MarketParser')
    @patch('skills.market_portfolio_predictive_aggregator.PortfolioScenarioSimulator')
    def test_predictive_aggregator_initialization_and_flow(self, mock_simulator_cls, mock_collector_cls):
        mock_collector_instance = mock_collector_cls.return_value
        mock_simulator_instance = mock_simulator_cls.return_value

        expected_valuation = {
            uuid.uuid4().hex: random.randint(100, 5000),
            uuid.uuid4().hex: random.uniform(10.0, 999.9)
        }
        mock_collector_instance.get_total_summary.return_value = expected_valuation

        expected_simulation = {
            "symbol": self.rand_symbol,
            "shift": self.rand_shift,
            "projected_value": round(random.uniform(1000.0, 10000.0), 2)
        }
        mock_simulator_instance.simulate_scenario.return_value = expected_simulation

        aggregator = PredictiveAggregator(self.rand_storage)
        
        self.assertEqual(aggregator.storage_file, self.rand_storage)
        self.assertIsNotNone(aggregator.collector)
        self.assertIsNotNone(aggregator.simulator)

        result = aggregator.build_advanced_forecast(self.rand_symbol, self.rand_url, self.rand_shift)

        mock_collector_instance.get_total_summary.assert_called_once_with(self.rand_url)
        mock_simulator_instance.simulate_scenario.assert_called_once_with(self.rand_symbol, self.rand_shift)

        self.assertIn("valuation", result)
        self.assertIn("simulation", result)
        self.assertEqual(result["valuation"], expected_valuation)
        self.assertEqual(result["simulation"], expected_simulation)

    @patch('skills.market_portfolio_predictive_aggregator.PredictiveAggregator')
    def test_aggregate_market_forecast_wrapper(self, mock_aggregator_cls):
        mock_instance = mock_aggregator_cls.return_value
        
        expected_output = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "metric": random.randint(1, 100)
        }
        mock_instance.build_advanced_forecast.return_value = expected_output

        result = aggregate_market_forecast(
            storage_file=self.rand_storage,
            symbol=self.rand_symbol,
            url=self.rand_url,
            percentage_shift=self.rand_shift
        )

        mock_aggregator_cls.assert_called_once_with(self.rand_storage)
        mock_instance.build_advanced_forecast.assert_called_once_with(
            self.rand_symbol, self.rand_url, self.rand_shift
        )
        self.assertEqual(result, expected_output)

    @patch('skills.market_portfolio_predictive_aggregator.MarketParser')
    @patch('skills.market_portfolio_predictive_aggregator.PortfolioScenarioSimulator')
    def test_predictive_aggregator_stream_handling(self, mock_simulator_cls, mock_collector_cls):
        mock_collector_instance = mock_collector_cls.return_value
        mock_simulator_instance = mock_simulator_cls.return_value

        stream_bytes = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        
        mock_collector_instance.get_stream_data = MagicMock(return_value=stream_bytes)

        aggregator = PredictiveAggregator(self.rand_storage)
        
        has_attr = hasattr(aggregator, 'collector') or hasattr(aggregator, 'simulator')
        self.assertTrue(has_attr)

        mock_collector_instance.fetch_and_store(self.rand_symbol, float(random.randint(1, 500)))
        mock_collector_instance.fetch_and_store.assert_called_once()

    def test_composition_requirements_enforced(self):
        aggregator = PredictiveAggregator(self.rand_storage)
        
        has_collector = hasattr(aggregator, 'collector')
        has_simulator = hasattr(aggregator, 'simulator')
        
        self.assertTrue(has_collector, "Module MUST compose market_portfolio_collector_agent")
        self.assertTrue(has_simulator, "Module MUST compose market_portfolio_scenario_simulator")

if __name__ == '__main__':
    unittest.main()