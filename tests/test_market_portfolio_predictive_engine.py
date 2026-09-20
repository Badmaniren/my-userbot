import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.market_portfolio_predictive_engine import PredictiveEngine, predict_future_trend

class TestMarketPortfolioPredictiveEngine(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/market"
        self.percentage_shift = round(random.uniform(-50.0, 50.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_predictive_engine_initialization(self):
        engine = PredictiveEngine(self.storage_file)
        self.assertEqual(engine.storage_file, self.storage_file)
        self.assertIsNotNone(engine.collector_agent)
        self.assertIsNotNone(engine.scenario_simulator)

    def test_predict_future_trend_success(self):
        mock_collected_data = {
            uuid.uuid4().hex: random.randint(100, 1000),
            self.symbol: random.randint(50, 500)
        }
        mock_simulation_result = {
            "symbol": self.symbol,
            "original_price": random.randint(100, 500),
            "shifted_price": random.randint(100, 600),
            "shift_percentage": self.percentage_shift,
            "trend_forecast": random.choice(["BULLISH", "BEARISH", "STABLE"])
        }

        with patch('skills.market_portfolio_collector_agent.MarketParser.load_data', return_value=mock_collected_data) as mock_load, \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.simulate_scenario', return_value=mock_simulation_result) as mock_sim:

            engine = PredictiveEngine(self.storage_file)
            result = engine.predict_future_trend(self.symbol, self.percentage_shift)

            mock_load.assert_called_once()
            mock_sim.assert_called_once_with(self.symbol, self.percentage_shift)

            self.assertIn("forecast_id", result)
            self.assertEqual(result["symbol"], self.symbol)
            self.assertEqual(result["simulation"], mock_simulation_result)
            self.assertIn("confidence_score", result)
            self.assertIsInstance(result["confidence_score"], float)

    def test_predictive_engine_empty_data_handling(self):
        with patch('skills.market_portfolio_collector_agent.MarketParser.load_data', return_value={}) as mock_load, \
             patch('skills.market_portfolio_scenario_simulator.PortfolioScenarioSimulator.simulate_scenario', return_value={}) as mock_sim:

            engine = PredictiveEngine(self.storage_file)
            result = engine.predict_future_trend(self.symbol, self.percentage_shift)

            self.assertEqual(result["symbol"], self.symbol)
            self.assertEqual(result["simulation"], {})
            self.assertEqual(result["confidence_score"], 0.0)

    def test_module_level_predict_future_trend_wrapper(self):
        expected_output = {
            "wrapper_run_id": uuid.uuid4().hex,
            "symbol": self.symbol,
            "trend": random.choice(["UP", "DOWN"])
        }

        with patch('skills.market_portfolio_predictive_engine.PredictiveEngine.predict_future_trend', return_value=expected_output) as mock_predict:
            res = predict_future_trend(self.storage_file, self.symbol, self.percentage_shift)
            mock_predict.assert_called_once_with(self.symbol, self.percentage_shift)
            self.assertEqual(res, expected_output)

    def test_stream_data_processing_in_engine(self):
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        mock_stream = io.BytesIO(random_bytes)

        with patch('skills.market_portfolio_collector_agent.StressReporter.get_stream_data', return_value=[mock_stream]) as mock_stream_data:
            engine = PredictiveEngine(self.storage_file)
            stream_dump = engine.analyze_market_stream()

            mock_stream_data.assert_called_once()
            self.assertIsInstance(stream_dump, list)
            self.assertTrue(len(stream_dump) > 0)

if __name__ == '__main__':
    unittest.main()