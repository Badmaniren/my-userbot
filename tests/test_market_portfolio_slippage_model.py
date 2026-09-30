import unittest
from unittest.mock import MagicMock, patch
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
        ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
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
        
        depth_factor = min(2.0, volume / max(available_liquidity, 1.0))
        expected = round(volume * volatility * 0.0001 * depth_factor, 6)

        self.assertIsInstance(result, float)
        self.assertEqual(result, expected)
        mock_parser.parse_market_depth.assert_called_once_with(ticker)

    def test_calculate_slippage_invalid_parameters_raises_error(self):
        invalid_cases = [
            OrderExecutionParameters(uuid.uuid4().hex, "", random.uniform(10, 100), random.uniform(0.1, 0.5)),
            OrderExecutionParameters(uuid.uuid4().hex, f"T_{uuid.uuid4().hex[:4]}", -1.0, random.uniform(0.1, 0.5)),
            OrderExecutionParameters(uuid.uuid4().hex, f"T_{uuid.uuid4().hex[:4]}", 0.0, random.uniform(0.1, 0.5)),
            OrderExecutionParameters(uuid.uuid4().hex, f"T_{uuid.uuid4().hex[:4]}", random.uniform(10, 100), 0.0),
            OrderExecutionParameters(uuid.uuid4().hex, f"T_{uuid.uuid4().hex[:4]}", random.uniform(10, 100), -0.5),
        ]

        for params in invalid_cases:
            with self.subTest(params=params):
                with self.assertRaises(SlippageCalculationError):
                    self.model.calculate_slippage(params)

    def test_fetch_external_liquidity_profile(self):
        ticker = f"SYM_{uuid.uuid4().hex[:5].upper()}"
        volume = random.uniform(50.0, 500.0)
        raw_bytes = f"data_{uuid.uuid4().hex}".encode('utf-8')

        mock_api_gateway = MagicMock()
        self.model.api_gateway = mock_api_gateway

        mock_response = MagicMock()
        mock_response.raw = io.BytesIO(raw_bytes)

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = self.model.fetch_external_liquidity_profile(ticker, volume)
            
            mock_get.assert_called_once_with(f"https://api.example.com/liquidity/{ticker}?volume={volume}")
            mock_api_gateway.log_request.assert_called_once_with(ticker, volume)
            self.assertEqual(result.read(), raw_bytes)

    def test_estimate_market_impact(self):
        ticker = f"AST_{uuid.uuid4().hex[:4].upper()}"
        volume = random.uniform(100.0, 2000.0)
        volatility = random.uniform(0.15, 0.85)
        multiplier = random.uniform(1.1, 3.5)

        params = OrderExecutionParameters(
            order_id=uuid.uuid4().hex,
            ticker=ticker,
            volume=volume,
            volatility=volatility
        )

        mock_anomaly_detector = MagicMock()
        anomaly_data = {"multiplier": multiplier, "reason": uuid.uuid4().hex}
        mock_anomaly_detector.detect.return_value = anomaly_data
        self.model.anomaly_detector = mock_anomaly_detector

        mock_alert_dispatcher = MagicMock()
        self.model.alert_dispatcher = mock_alert_dispatcher

        impact = self.model.estimate_market_impact(params)

        expected = float(volume * volatility * 0.00005 * multiplier)
        self.assertIsInstance(impact, float)
        self.assertEqual(impact, expected)
        mock_anomaly_detector.detect.assert_called_once_with(ticker)
        mock_alert_dispatcher.dispatch.assert_called_once_with(anomaly_data)

    def test_simulate_stress_slippage(self):
        ticker = f"ST_{uuid.uuid4().hex[:4].upper()}"
        volume = random.uniform(1000.0, 5000.0)
        scenario_name = f"scenario_{uuid.uuid4().hex[:8]}"
        stress_mult = random.uniform(1.5, 4.0)

        mock_pipeline = MagicMock()
        mock_pipeline.run_simulation.return_value = {"stress_multiplier": stress_mult}
        self.model.stress_scenario_pipeline = mock_pipeline

        result = self.model.simulate_stress_slippage(ticker, volume, scenario_name)

        expected_slippage = round(volume * 0.2 * 0.0001 * stress_mult, 6)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["scenario"], scenario_name)
        self.assertEqual(result["stress_multiplier"], stress_mult)
        self.assertEqual(result["adjusted_slippage"], expected_slippage)
        mock_pipeline.run_simulation.assert_called_once_with(scenario_name)

    def test_simulate_order_execution_buy(self):
        order_id = uuid.uuid4().hex
        symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        quantity = random.uniform(100.0, 1000.0)
        price = random.uniform(50.0, 200.0)

        order_data = {
            "order_id": order_id,
            "symbol": symbol,
            "side": "BUY",
            "quantity": quantity,
            "price": price
        }

        adv = random.uniform(10000.0, 500000.0)
        volatility = random.uniform(0.1, 0.4)
        spread_bps = random.uniform(1.0, 10.0)

        market_context = {
            "adv": adv,
            "volatility": volatility,
            "spread_bps": spread_bps
        }

        result = self.model.simulate_order_execution(order_data, market_context)

        self.assertEqual(result["order_id"], order_id)
        self.assertEqual(result["symbol"], symbol)
        self.assertEqual(result["side"], "BUY")
        self.assertEqual(result["status"], "FILLED")
        self.assertIn("executed_price", result)
        self.assertIn("realized_cost", result)
        self.assertGreater(result["executed_price"], price)

    def test_simulate_order_execution_sell(self):
        order_id = uuid.uuid4().hex
        symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        quantity = random.uniform(100.0, 1000.0)
        price = random.uniform(50.0, 200.0)

        order_data = {
            "order_id": order_id,
            "symbol": symbol,
            "side": "SELL",
            "quantity": quantity,
            "price": price
        }

        market_context = {
            "adv": 100000,
            "volatility": 0.2,
            "spread_bps": 5.0
        }

        result = self.model.simulate_order_execution(order_data, market_context)

        self.assertEqual(result["side"], "SELL")
        self.assertLess(result["executed_price"], price)

    def test_simulate_batch(self):
        sym_1 = f"S1_{uuid.uuid4().hex[:3].upper()}"
        sym_2 = f"S2_{uuid.uuid4().hex[:3].upper()}"

        orders = [
            {"order_id": uuid.uuid4().hex, "symbol": sym_1, "side": "BUY", "quantity": 100, "price": 10.0},
            {"order_id": uuid.uuid4().hex, "symbol": sym_2, "side": "SELL", "quantity": 200, "price": 20.0},
        ]

        contexts = {
            sym_1: {"adv": 50000, "volatility": 0.1, "spread_bps": 2.0},
            sym_2: {"adv": 80000, "volatility": 0.3, "spread_bps": 4.0},
        }

        results = self.model.simulate_batch(orders, contexts)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["symbol"], sym_1)
        self.assertEqual(results[1]["symbol"], sym_2)
        self.assertEqual(results[0]["status"], "FILLED")
        self.assertEqual(results[1]["status"], "FILLED")

    def test_persist_and_get_execution_logs(self):
        sim_id = uuid.uuid4().hex
        executions = [
            {"order_id": uuid.uuid4().hex, "symbol": f"SYM_{uuid.uuid4().hex[:3]}", "status": "FILLED"}
        ]

        mock_storage = MagicMock()
        mock_storage.get_logs.return_value = executions

        persist_res = self.model.persist_execution_logs(sim_id, executions, mock_storage)
        self.assertTrue(persist_res)

        # Get from internal cache
        cached_logs = self.model.get_execution_logs(sim_id, mock_storage)
        self.assertEqual(cached_logs, executions)

        # Get from storage when not in cache
        new_sim_id = uuid.uuid4().hex
        storage_logs = self.model.get_execution_logs(new_sim_id, mock_storage)
        self.assertEqual(storage_logs, executions)
        mock_storage.get_logs.assert_called_once_with(new_sim_id)

    def test_get_execution_logs_empty(self):
        sim_id = uuid.uuid4().hex
        mock_storage = MagicMock()
        mock_storage.get_logs.return_value = []

        logs = self.model.get_execution_logs(sim_id, mock_storage)
        self.assertEqual(logs, [])


if __name__ == "__main__":
    unittest.main()