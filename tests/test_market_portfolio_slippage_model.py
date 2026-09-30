import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
from skills.market_portfolio_slippage_model import MarketPortfolioSlippageModel, OrderExecutionParameters, SlippageCalculationError

class TestMarketPortfolioSlippageModel(unittest.TestCase):
    def setUp(self):
        self.model = MarketPortfolioSlippageModel()
        self.ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.volume = random.uniform(100.0, 10000.0)
        self.volatility = random.uniform(0.01, 0.5)
        self.order_id = uuid.uuid4().hex

    def test_calculate_slippage_success(self):
        params = OrderExecutionParameters(self.order_id, self.ticker, self.volume, self.volatility)
        mock_parser = MagicMock()
        self.model.market_parser = mock_parser
        
        result = self.model.calculate_slippage(params)
        
        expected = round(self.volume * self.volatility * 0.0001, 6)
        self.assertEqual(result, expected)
        mock_parser.parse_market_depth.assert_called_once_with(self.ticker)

    def test_calculate_slippage_invalid_params(self):
        params = OrderExecutionParameters(self.order_id, self.ticker, -1.0, self.volatility)
        with self.assertRaises(SlippageCalculationError):
            self.model.calculate_slippage(params)

    def test_fetch_external_liquidity_profile_success(self):
        mock_gateway = MagicMock()
        self.model.market_portfolio_api_gateway = mock_gateway
        random_bytes = uuid.uuid4().bytes
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raw = io.BytesIO(random_bytes)
            mock_get.return_value = mock_response
            
            result = self.model.fetch_external_liquidity_profile(self.ticker, self.volume)
            
            self.assertEqual(result.read(), random_bytes)
            mock_gateway.log_request.assert_called_once_with(self.ticker, self.volume)

    def test_estimate_market_impact_with_anomaly(self):
        params = OrderExecutionParameters(self.order_id, self.ticker, self.volume, self.volatility)
        mock_detector = MagicMock()
        multiplier = random.uniform(1.1, 5.0)
        mock_detector.detect.return_value = {"multiplier": multiplier}
        self.model.anomaly_detector = mock_detector
        
        mock_dispatcher = MagicMock()
        self.model.alert_dispatcher = mock_dispatcher
        
        result = self.model.estimate_market_impact(params)
        expected = self.volume * self.volatility * 0.00005 * multiplier
        self.assertAlmostEqual(result, expected, places=6)
        mock_dispatcher.dispatch.assert_called_once()

    def test_simulate_order_execution_logic(self):
        order_data = {
            "order_id": uuid.uuid4().hex,
            "symbol": self.ticker,
            "side": random.choice(["BUY", "SELL"]),
            "quantity": random.uniform(10, 1000),
            "price": random.uniform(50.0, 500.0)
        }
        context = {
            "adv": random.uniform(50000, 200000),
            "volatility": 0.2,
            "spread_bps": 5.0
        }
        
        result = self.model.simulate_order_execution(order_data, context)
        
        self.assertEqual(result["order_id"], order_data["order_id"])
        self.assertEqual(result["status"], "FILLED")
        self.assertIn("realized_cost", result)
        self.assertIsInstance(result["slippage_bps"], float)

    def test_persist_and_get_logs(self):
        sim_id = uuid.uuid4().hex
        logs = [{"id": uuid.uuid4().hex, "val": random.random()}]
        mock_storage = MagicMock()
        
        self.model.persist_execution_logs(sim_id, logs, mock_storage)
        retrieved = self.model.get_execution_logs(sim_id, mock_storage)
        
        self.assertEqual(retrieved, logs)
        mock_storage.save_logs.assert_called_once_with(sim_id, logs)

    def test_simulate_stress_slippage(self):
        scenario = uuid.uuid4().hex
        stress_val = random.uniform(1.5, 3.0)
        mock_pipeline = MagicMock()
        mock_pipeline.run_simulation.return_value = {"stress_multiplier": stress_val}
        self.model.stress_scenario_pipeline = mock_pipeline
        
        result = self.model.simulate_stress_slippage(self.ticker, self.volume, scenario)
        
        self.assertEqual(result["scenario"], scenario)
        self.assertEqual(result["stress_multiplier"], stress_val)
        expected_slippage = round(self.volume * 0.2 * 0.0001 * stress_val, 6)
        self.assertEqual(result["adjusted_slippage"], expected_slippage)

if __name__ == '__main__':
    unittest.main()