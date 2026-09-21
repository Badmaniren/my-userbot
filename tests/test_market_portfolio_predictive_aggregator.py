import unittest
from unittest.mock import patch
import uuid
import random
from skills.market_portfolio_predictive_aggregator import (
    PredictiveAggregator,
    MarketPortfolioPredictiveAggregator,
    aggregate_market_forecast
)


class TestPredictiveAggregator(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex}"
        self.shift = round(random.uniform(-50.0, 50.0), 2)

    def test_init_and_aliases(self):
        aggregator = PredictiveAggregator(self.storage_file)
        self.assertEqual(aggregator.storage_file, self.storage_file)
        self.assertIs(MarketPortfolioPredictiveAggregator, PredictiveAggregator)

    def test_build_advanced_forecast_success(self):
        expected_valuation = {uuid.uuid4().hex: random.randint(100, 1000)}
        expected_simulation = {
            "symbol": self.symbol,
            "shift": self.shift,
            "projected_value": round(random.uniform(10.0, 500.0), 2)
        }

        with patch("skills.market_portfolio_predictive_aggregator.MarketParser") as MockParser, \
             patch("skills.market_portfolio_predictive_aggregator.PortfolioScenarioSimulator") as MockSimulator:

            instance_parser = MockParser.return_value
            instance_parser.get_total_summary.return_value = expected_valuation

            instance_simulator = MockSimulator.return_value
            instance_simulator.simulate_scenario.return_value = expected_simulation

            aggregator = PredictiveAggregator(self.storage_file)
            result = aggregator.build_advanced_forecast(self.symbol, self.url, self.shift)

            instance_parser.get_total_summary.assert_called_once_with(self.url)
            instance_simulator.simulate_scenario.assert_called_once_with(self.symbol, self.shift)

            self.assertEqual(result["valuation"], expected_valuation)
            self.assertEqual(result["simulation"], expected_simulation)

    def test_build_advanced_forecast_valuation_missing_method(self):
        expected_simulation = {
            "symbol": self.symbol,
            "shift": self.shift,
            "projected_value": round(random.uniform(1.0, 100.0), 2)
        }

        with patch("skills.market_portfolio_predictive_aggregator.MarketParser") as MockParser, \
             patch("skills.market_portfolio_predictive_aggregator.PortfolioScenarioSimulator") as MockSimulator:

            instance_parser = MockParser.return_value
            del instance_parser.get_total_summary

            instance_simulator = MockSimulator.return_value
            instance_simulator.simulate_scenario.return_value = expected_simulation

            aggregator = PredictiveAggregator(self.storage_file)
            result = aggregator.build_advanced_forecast(self.symbol, self.url, self.shift)

            self.assertEqual(result["valuation"], {})
            self.assertEqual(result["simulation"], expected_simulation)

    def test_build_advanced_forecast_simulation_key_error(self):
        expected_valuation = {uuid.uuid4().hex: random.randint(10, 50)}

        with patch("skills.market_portfolio_predictive_aggregator.MarketParser") as MockParser, \
             patch("skills.market_portfolio_predictive_aggregator.PortfolioScenarioSimulator") as MockSimulator:

            instance_parser = MockParser.return_value
            instance_parser.get_total_summary.return_value = expected_valuation

            instance_simulator = MockSimulator.return_value
            instance_simulator.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)

            aggregator = PredictiveAggregator(self.storage_file)
            result = aggregator.build_advanced_forecast(self.symbol, self.url, self.shift)

            self.assertEqual(result["valuation"], expected_valuation)
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["shift"], self.shift)
            self.assertEqual(result["simulation"]["projected_value"], 0.0)

    def test_build_predictive_forecast_delegation(self):
        expected_valuation = {uuid.uuid4().hex: random.randint(200, 800)}
        expected_simulation = {
            "symbol": self.symbol,
            "shift": self.shift,
            "projected_value": round(random.uniform(50.0, 250.0), 2)
        }

        with patch("skills.market_portfolio_predictive_aggregator.MarketParser") as MockParser, \
             patch("skills.market_portfolio_predictive_aggregator.PortfolioScenarioSimulator") as MockSimulator:

            instance_parser = MockParser.return_value
            instance_parser.get_total_summary.return_value = expected_valuation

            instance_simulator = MockSimulator.return_value
            instance_simulator.simulate_scenario.return_value = expected_simulation

            aggregator = PredictiveAggregator(self.storage_file)
            result = aggregator.build_predictive_forecast(self.symbol, self.url, self.shift)

            self.assertEqual(result["valuation"], expected_valuation)
            self.assertEqual(result["simulation"], expected_simulation)

    def test_aggregate_market_forecast_helper_function(self):
        expected_valuation = {uuid.uuid4().hex: random.randint(50, 500)}
        expected_simulation = {
            "symbol": self.symbol,
            "shift": self.shift,
            "projected_value": round(random.uniform(5.0, 75.0), 2)
        }

        with patch("skills.market_portfolio_predictive_aggregator.MarketParser") as MockParser, \
             patch("skills.market_portfolio_predictive_aggregator.PortfolioScenarioSimulator") as MockSimulator:

            instance_parser = MockParser.return_value
            instance_parser.get_total_summary.return_value = expected_valuation

            instance_simulator = MockSimulator.return_value
            instance_simulator.simulate_scenario.return_value = expected_simulation

            result = aggregate_market_forecast(self.storage_file, self.symbol, self.url, self.shift)

            self.assertEqual(result["valuation"], expected_valuation)
            self.assertEqual(result["simulation"], expected_simulation)


if __name__ == "__main__":
    unittest.main()