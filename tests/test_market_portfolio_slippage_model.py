import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_slippage_model import (
    MarketPortfolioSlippageModel,
    OrderExecutionParameters,
    SlippageCalculationError
)

class TestMarketPortfolioSlippageModel(unittest.TestCase):
    def setUp(self):
        self.model = MarketPortfolioSlippageModel()

    def test_calculate_slippage_success(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        volume = random.uniform(10.0, 1000.0)
        volatility = random.uniform(0.1, 0.9)
        
        params = OrderExecutionParameters(
            order_id=uuid.uuid4().hex,
            ticker=ticker,
            volume=volume,
            volatility=volatility
        )
        
        mock_parser = MagicMock()
        available_liquidity = volume * random.uniform(5.0, 15.0)
        mock_parser.parse_market_depth.return_value = {"total_depth": available_liquidity}
        self.model.market_parser = mock_parser
        
        result = self.model.calculate_slippage(params)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0.0)

    def test_calculate_slippage_invalid_params(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        params = OrderExecutionParameters(
            order_id=uuid.uuid4().hex,
            ticker=ticker,
            volume=-10.0,
            volatility=0.2
        )
        
        with self.assertRaises(SlippageCalculationError):
            self.model.calculate_slippage(params)

    def test_fetch_external_liquidity_profile(self):
        ticker = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        volume = random.uniform(50.0, 500.0)
        
        mock_api_gateway = MagicMock()
        self.model.api_gateway = mock_api_gateway
        
        random_bytes = f"data_{uuid.uuid4().hex}".encode('utf-8')
        mock_response = MagicMock()
        mock_response.raw = io.BytesIO(random_bytes)
        
        with patch('skills.market_portfolio_slippage_model.requests.get', return_value=mock_response) as mock_get:
            result = self.model.fetch_external_liquidity_profile(ticker, volume)
            mock_get.assert_called_once()
            mock_api_gateway.log_request.assert_called_once_with(ticker, volume)
            self.assertIsInstance(result, io.BytesIO)
            self.assertEqual(result.read(), random_bytes)

    def test_estimate_market_impact(self):
        ticker = f"ASSET_{uuid.uuid4().hex[:6].upper()}"
        volume = random.uniform(100.0, 10000.0)
        volatility = random.uniform(0.1, 0.5)
        multiplier = random.uniform(1.1, 3.0)
        
        params = OrderExecutionParameters(
            order_id=uuid.uuid4().hex,
            ticker=ticker,
            volume=volume,
            volatility=volatility
        )
        
        mock_anomaly_detector = MagicMock()
        mock_anomaly_detector.detect.return_value = {"multiplier": multiplier}
        mock_alert_dispatcher = MagicMock()
        
        self.model.anomaly_detector = mock_anomaly_detector
        self.model.alert_dispatcher = mock_alert_dispatcher
        
        impact = self.model.estimate_market_impact(params)
        
        mock_anomaly_detector.detect.assert_called_once_with(ticker)
        mock_alert_dispatcher.dispatch.assert_called_once()
        expected = float(volume * volatility * 0.00005 * multiplier)
        self.assertAlmostEqual(impact, expected, places=5)

    def test_simulate_stress_slippage(self):
        ticker = f"ST_{uuid.uuid4().hex[:6].upper()}"
        volume = random.uniform(1000.0, 5000.0)
        scenario = f"scenario_{uuid.uuid4().hex[:8]}"
        stress_mult = random.uniform(1.5, 4.0)
        
        mock_pipeline = MagicMock()
        mock_pipeline.run_simulation.return_value = {"stress_multiplier": stress_mult}
        self.model.stress_scenario_pipeline = mock_pipeline
        
        res = self.model.simulate_stress_slippage(ticker, volume, scenario)
        
        self.assertEqual(res["scenario"], scenario)
        self.assertEqual(res["stress_multiplier"], stress_mult)
        self.assertIn("adjusted_slippage", res)
        self.assertGreater(res["adjusted_slippage"], 0.0)

    def test_simulate_order_execution_buy(self):
        order_id = uuid.uuid4().hex
        symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        quantity = random.randint(100, 1000)
        base_price = round(random.uniform(50.0, 200.0), 2)
        
        order_data = {
            "order_id": order_id,
            "symbol": symbol,
            "side": "BUY",
            "quantity": quantity,
            "price": base_price
        }
        
        market_context = {
            "adv": 500000,
            "volatility": 0.25,
            "spread_bps": 6.0
        }
        
        res = self.model.simulate_order_execution(order_data, market_context)
        
        self.assertEqual(res["order_id"], order_id)
        self.assertEqual(res["symbol"], symbol)
        self.assertEqual(res["side"], "BUY")
        self.assertEqual(res["quantity"], quantity)
        self.assertEqual(res["price"], base_price)
        self.assertEqual(res["status"], "FILLED")
        self.assertGreater(res["executed_price"], base_price)

    def test_simulate_order_execution_sell(self):
        order_id = uuid.uuid4().hex
        symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        quantity = random.randint(100, 1000)
        base_price = round(random.uniform(50.0, 200.0), 2)
        
        order_data = {
            "order_id": order_id,
            "symbol": symbol,
            "side": "SELL",
            "quantity": quantity,
            "price": base_price
        }
        
        market_context = {
            "adv": 500000,
            "volatility": 0.25,
            "spread_bps": 6.0
        }
        
        res = self.model.simulate_order_execution(order_data, market_context)
        
        self.assertEqual(res["order_id"], order_id)
        self.assertEqual(res["symbol"], symbol)
        self.assertEqual(res["side"], "SELL")
        self.assertEqual(res["quantity"], quantity)
        self.assertEqual(res["price"], base_price)
        self.assertEqual(res["status"], "FILLED")
        self.assertLess(res["executed_price"], base_price)

    def test_simulate_batch(self):
        sym1 = f"S1_{uuid.uuid4().hex[:4].upper()}"
        sym2 = f"S2_{uuid.uuid4().hex[:4].upper()}"
        
        orders = [
            {"order_id": uuid.uuid4().hex, "symbol": sym1, "side": "BUY", "quantity": 200, "price": 100.0},
            {"order_id": uuid.uuid4().hex, "symbol": sym2, "side": "SELL", "quantity": 300, "price": 150.0}
        ]
        
        contexts = {
            sym1: {"adv": 100000, "volatility": 0.2, "spread_bps": 5.0},
            sym2: {"adv": 200000, "volatility": 0.3, "spread_bps": 4.0}
        }
        
        results = self.model.simulate_batch(orders, contexts)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["symbol"], sym1)
        self.assertEqual(results[1]["symbol"], sym2)

    def test_persist_and_get_execution_logs_internal(self):
        sim_id = uuid.uuid4().hex
        executions = [{"order_id": uuid.uuid4().hex, "status": "FILLED"}]
        
        storage = MagicMock()
        success = self.model.persist_execution_logs(sim_id, executions, storage)
        self.assertTrue(success)
        
        logs = self.model.get_execution_logs(sim_id, storage)
        self.assertEqual(logs, executions)
        storage.save_logs.assert_called_once_with(sim_id, executions)

    def test_get_execution_logs_from_storage(self):
        sim_id = uuid.uuid4().hex
        executions = [{"order_id": uuid.uuid4().hex, "status": "FILLED"}]
        
        storage = MagicMock()
        storage.get_logs.return_value = executions
        
        logs = self.model.get_execution_logs(sim_id, storage)
        self.assertEqual(logs, executions)
        storage.get_logs.assert_called_once_with(sim_id)