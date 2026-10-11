import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
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
        rand_order_id = uuid.uuid4().hex
        rand_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        rand_volume = random.uniform(100.0, 10000.0)
        rand_volatility = random.uniform(0.1, 0.9)

        params = OrderExecutionParameters(
            order_id=rand_order_id,
            ticker=rand_ticker,
            volume=rand_volume,
            volatility=rand_volatility
        )

        market_parser_mock = MagicMock()
        rand_depth = random.uniform(50000.0, 200000.0)
        market_parser_mock.parse_market_depth.return_value = {"total_depth": rand_depth}
        self.model.market_parser = market_parser_mock

        result = self.model.calculate_slippage(params)

        self.assertIsInstance(result, float)
        self.assertGreater(result, 0.0)
        market_parser_mock.parse_market_depth.assert_called_once_with(rand_ticker)

    def test_calculate_slippage_invalid_params(self):
        rand_order_id = uuid.uuid4().hex
        rand_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"

        params_zero_vol = OrderExecutionParameters(
            order_id=rand_order_id,
            ticker=rand_ticker,
            volume=100.0,
            volatility=0.0
        )

        with self.assertRaises(SlippageCalculationError):
            self.model.calculate_slippage(params_zero_vol)

        params_negative_vol = OrderExecutionParameters(
            order_id=rand_order_id,
            ticker=rand_ticker,
            volume=-50.0,
            volatility=0.2
        )

        with self.assertRaises(SlippageCalculationError):
            self.model.calculate_slippage(params_negative_vol)

        params_empty_ticker = OrderExecutionParameters(
            order_id=rand_order_id,
            ticker="",
            volume=100.0,
            volatility=0.2
        )

        with self.assertRaises(SlippageCalculationError):
            self.model.calculate_slippage(params_empty_ticker)

    def test_fetch_external_liquidity_profile(self):
        rand_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        rand_volume = random.uniform(1000.0, 50000.0)
        rand_content = uuid.uuid4().bytes

        api_gateway_mock = MagicMock()
        self.model.api_gateway = api_gateway_mock

        with patch("skills.market_portfolio_slippage_model.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raw = io.BytesIO(rand_content)
            mock_get.return_value = mock_response

            result = self.model.fetch_external_liquidity_profile(rand_ticker, rand_volume)

            self.assertIsInstance(result, io.BytesIO)
            self.assertEqual(result.read(), rand_content)
            api_gateway_mock.log_request.assert_called_once_with(rand_ticker, rand_volume)

    def test_estimate_market_impact(self):
        rand_order_id = uuid.uuid4().hex
        rand_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        rand_volume = random.uniform(500.0, 5000.0)
        rand_volatility = random.uniform(0.1, 0.5)
        rand_multiplier = random.uniform(1.2, 3.5)

        params = OrderExecutionParameters(
            order_id=rand_order_id,
            ticker=rand_ticker,
            volume=rand_volume,
            volatility=rand_volatility
        )

        anomaly_detector_mock = MagicMock()
        anomaly_data = {"multiplier": rand_multiplier}
        anomaly_detector_mock.detect.return_value = anomaly_data
        self.model.anomaly_detector = anomaly_detector_mock

        alert_dispatcher_mock = MagicMock()
        self.model.alert_dispatcher = alert_dispatcher_mock

        impact = self.model.estimate_market_impact(params)

        self.assertIsInstance(impact, float)
        expected_impact = float(rand_volume * rand_volatility * 0.00005 * rand_multiplier)
        self.assertAlmostEqual(impact, expected_impact)
        anomaly_detector_mock.detect.assert_called_once_with(rand_ticker)
        alert_dispatcher_mock.dispatch.assert_called_once_with(anomaly_data)

    def test_simulate_stress_slippage(self):
        rand_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        rand_volume = random.uniform(1000.0, 10000.0)
        rand_scenario = f"SCENARIO_{uuid.uuid4().hex[:8]}"
        rand_multiplier = random.uniform(1.5, 4.0)

        pipeline_mock = MagicMock()
        pipeline_mock.run_simulation.return_value = {"stress_multiplier": rand_multiplier}
        self.model.stress_scenario_pipeline = pipeline_mock

        result = self.model.simulate_stress_slippage(rand_ticker, rand_volume, rand_scenario)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["scenario"], rand_scenario)
        self.assertEqual(result["stress_multiplier"], rand_multiplier)
        expected_slippage = round(rand_volume * 0.2 * 0.0001 * rand_multiplier, 6)
        self.assertEqual(result["adjusted_slippage"], expected_slippage)
        pipeline_mock.run_simulation.assert_called_once_with(rand_scenario)

    def test_simulate_order_execution_buy(self):
        rand_order_id = uuid.uuid4().hex
        rand_symbol = f"SYM_{uuid.uuid4().hex[:5].upper()}"
        rand_quantity = random.uniform(500.0, 2000.0)
        rand_price = random.uniform(50.0, 500.0)

        order_data = {
            "order_id": rand_order_id,
            "symbol": rand_symbol,
            "side": "BUY",
            "quantity": rand_quantity,
            "price": rand_price
        }
        market_context = {
            "adv": 500000.0,
            "volatility": 0.25,
            "spread_bps": 6.0
        }

        result = self.model.simulate_order_execution(order_data, market_context)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["order_id"], rand_order_id)
        self.assertEqual(result["symbol"], rand_symbol)
        self.assertEqual(result["side"], "BUY")
        self.assertEqual(result["status"], "FILLED")
        self.assertGreater(result["executed_price"], rand_price)
        self.assertGreater(result["realized_cost"], 0.0)

    def test_simulate_order_execution_sell(self):
        rand_order_id = uuid.uuid4().hex
        rand_symbol = f"SYM_{uuid.uuid4().hex[:5].upper()}"
        rand_quantity = random.uniform(500.0, 2000.0)
        rand_price = random.uniform(50.0, 500.0)

        order_data = {
            "order_id": rand_order_id,
            "symbol": rand_symbol,
            "side": "SELL",
            "quantity": rand_quantity,
            "price": rand_price
        }
        market_context = {
            "adv": 500000.0,
            "volatility": 0.25,
            "spread_bps": 6.0
        }

        result = self.model.simulate_order_execution(order_data, market_context)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["side"], "SELL")
        self.assertLess(result["executed_price"], rand_price)

    def test_simulate_batch(self):
        rand_symbol_1 = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        rand_symbol_2 = f"SYM_{uuid.uuid4().hex[:4].upper()}"

        orders_batch = [
            {"order_id": uuid.uuid4().hex, "symbol": rand_symbol_1, "side": "BUY", "quantity": 100.0, "price": 10.0},
            {"order_id": uuid.uuid4().hex, "symbol": rand_symbol_2, "side": "SELL", "quantity": 200.0, "price": 20.0}
        ]
        contexts = {
            rand_symbol_1: {"adv": 10000, "volatility": 0.1, "spread_bps": 2.0},
            rand_symbol_2: {"adv": 20000, "volatility": 0.15, "spread_bps": 3.0}
        }

        results = self.model.simulate_batch(orders_batch, contexts)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["order_id"], orders_batch[0]["order_id"])
        self.assertEqual(results[1]["order_id"], orders_batch[1]["order_id"])

    def test_persist_and_get_execution_logs(self):
        rand_sim_id = uuid.uuid4().hex
        rand_logs = [{"execution_id": uuid.uuid4().hex, "cost": random.uniform(10.0, 100.0)}]

        storage_mock = MagicMock()

        persist_res = self.model.persist_execution_logs(rand_sim_id, rand_logs, storage_mock)
        self.assertTrue(persist_res)
        storage_mock.save_logs.assert_called_once_with(rand_sim_id, rand_logs)

        retrieved_local = self.model.get_execution_logs(rand_sim_id, storage_mock)
        self.assertEqual(retrieved_local, rand_logs)

        model_empty = MarketPortfolioSlippageModel()
        storage_mock.get_logs.return_value = rand_logs
        retrieved_storage = model_empty.get_execution_logs(rand_sim_id, storage_mock)
        self.assertEqual(retrieved_storage, rand_logs)
        storage_mock.get_logs.assert_called_once_with(rand_sim_id)