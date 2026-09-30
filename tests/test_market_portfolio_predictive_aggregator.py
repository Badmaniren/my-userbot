import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.market_portfolio_predictive_aggregator import PredictiveAggregator

class TestPredictiveAggregator(unittest.TestCase):
    def setUp(self):
        self.storage_path = f"/tmp/{uuid.uuid4().hex}.db"
        self.aggregator = PredictiveAggregator(self.storage_path)

    def test_build_advanced_forecast_success(self):
        symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        url = f"https://{uuid.uuid4().hex}.com/api"
        shift = random.uniform(-0.5, 0.5)

        expected_valuation = {"total": random.random()}
        expected_simulation = {
            "symbol": symbol,
            "shift": shift,
            "projected_value": random.uniform(100, 1000)
        }

        with patch('skills.market_portfolio_collector_agent.MarketParser') as MockParser:
            with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator') as MockSimulator:
                instance_parser = MockParser.return_value
                instance_parser.get_total_summary.return_value = expected_valuation

                instance_sim = MockSimulator.return_value
                instance_sim.simulate_scenario.return_value = expected_simulation

                aggregator = PredictiveAggregator(self.storage_path)
                result = aggregator.build_advanced_forecast(symbol, url, shift)

                self.assertEqual(result["valuation"], expected_valuation)
                self.assertEqual(result["simulation"]["projected_value"], expected_simulation["projected_value"])
                self.assertEqual(result["simulation"]["symbol"], symbol)

    def test_build_advanced_forecast_missing_simulation_data(self):
        symbol = uuid.uuid4().hex[:5]
        url = f"http://{uuid.uuid4().hex}.io"
        shift = random.uniform(0.1, 0.9)

        with patch('skills.market_portfolio_collector_agent.MarketParser') as MockParser:
            with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator') as MockSimulator:
                MockParser.return_value.get_total_summary.return_value = {}
                MockSimulator.return_value.simulate_scenario.return_value = None

                aggregator = PredictiveAggregator(self.storage_path)
                result = aggregator.build_advanced_forecast(symbol, url, shift)

                self.assertEqual(result["simulation"]["symbol"], symbol)
                self.assertEqual(result["simulation"]["shift"], shift)
                self.assertEqual(result["simulation"]["projected_value"], 0.0)

    def test_build_advanced_forecast_exception_handling(self):
        symbol = uuid.uuid4().hex
        url = uuid.uuid4().hex
        shift = random.random()

        with patch('skills.market_portfolio_collector_agent.MarketParser') as MockParser:
            with patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator') as MockSimulator:
                MockSimulator.return_value.simulate_scenario.side_effect = KeyError("Sim fail")

                aggregator = PredictiveAggregator(self.storage_path)
                result = aggregator.build_advanced_forecast(symbol, url, shift)

                self.assertEqual(result["simulation"]["symbol"], symbol)
                self.assertEqual(result["simulation"]["projected_value"], 0.0)

    def test_aggregate_market_forecast_integration(self):
        # Тест функции-обертки
        symbol = uuid.uuid4().hex
        url = uuid.uuid4().hex
        shift = random.random()

        with patch('skills.market_portfolio_predictive_aggregator.PredictiveAggregator') as MockAggregator:
            from skills.market_portfolio_predictive_aggregator import aggregate_market_forecast

            mock_instance = MockAggregator.return_value
            mock_instance.build_advanced_forecast.return_value = {"status": "ok"}

            res = aggregate_market_forecast(self.storage_path, symbol, url, shift)

            self.assertEqual(res["status"], "ok")
            MockAggregator.assert_called_once_with(self.storage_path)

if __name__ == '__main__':
    unittest.main()