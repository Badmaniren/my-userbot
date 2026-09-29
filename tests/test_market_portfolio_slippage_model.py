import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import requests

from skills.market_portfolio_slippage_model import (
    MarketPortfolioSlippageModel,
    OrderExecutionParameters,
    SlippageCalculationError
)


class TestMarketPortfolioSlippageModel(unittest.TestCase):

    def setUp(self):
        self.ticker = uuid.uuid4().hex[:6].upper()
        self.order_id = uuid.uuid4().hex
        self.volume = round(random.uniform(100.0, 10000.0), 2)
        self.volatility = round(random.uniform(0.01, 0.5), 4)
        self.scenario_name = f"scenario_{uuid.uuid4().hex[:8]}"

    def test_calculate_slippage_success(self):
        market_parser_mock = MagicMock()
        audit_notifier_mock = MagicMock()
        
        model = MarketPortfolioSlippageModel(
            market_parser=market_parser_mock,
            audit_notifier=audit_notifier_mock
        )
        
        params = OrderExecutionParameters(
            order_id=self.order_id,
            ticker=self.ticker,
            volume=self.volume,
            volatility=self.volatility
        )
        
        result = model.calculate_slippage(params)
        
        market_parser_mock.parse_market_depth.assert_called_once_with(self.ticker)
        audit_notifier_mock.notify_error.assert_not_called()
        
        expected = round(self.volume * self.volatility * 0.0001, 6)
        self.assertEqual(result, expected)

    def test_calculate_slippage_invalid_parameters_raises_error(self):
        audit_notifier_mock = MagicMock()
        model = MarketPortfolioSlippageModel(audit_notifier=audit_notifier_mock)
        
        invalid_params = OrderExecutionParameters(
            order_id=self.order_id,
            ticker="",
            volume=self.volume,
            volatility=self.volatility
        )
        
        with self.assertRaises(SlippageCalculationError):
            model.calculate_slippage(invalid_params)
        
        audit_notifier_mock.notify_error.assert_called_once()

    def test_fetch_external_liquidity_profile_success(self):
        api_gateway_mock = MagicMock()
        model = MarketPortfolioSlippageModel(api_gateway=api_gateway_mock)
        
        random_bytes = io.BytesIO(uuid.uuid4().bytes)
        
        with patch("skills.market_portfolio_slippage_model.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raw = random_bytes
            mock_get.return_value = mock_response
            
            result = model.fetch_external_liquidity_profile(self.ticker, self.volume)
            
            mock_get.assert_called_once_with(f"https://api.example.com/liquidity/{self.ticker}?volume={self.volume}")
            api_gateway_mock.log_request.assert_called_once_with(self.ticker, self.volume)
            self.assertEqual(result, random_bytes)

    def test_fetch_external_liquidity_profile_exception(self):
        api_gateway_mock = MagicMock()
        model = MarketPortfolioSlippageModel(api_gateway=api_gateway_mock)
        
        with patch("skills.market_portfolio_slippage_model.requests.get", side_effect=requests.RequestException):
            result = model.fetch_external_liquidity_profile(self.ticker, self.volume)
            
            api_gateway_mock.log_request.assert_called_once_with(self.ticker, self.volume)
            self.assertIsNone(result)

    def test_estimate_market_impact(self):
        anomaly_detector_mock = MagicMock()
        alert_dispatcher_mock = MagicMock()
        
        multiplier = round(random.uniform(1.1, 3.0), 2)
        anomaly_dict = {"multiplier": multiplier, "reason": uuid.uuid4().hex}
        anomaly_detector_mock.detect.return_value = anomaly_dict
        
        model = MarketPortfolioSlippageModel(
            anomaly_detector=anomaly_detector_mock,
            alert_dispatcher=alert_dispatcher_mock
        )
        
        params = OrderExecutionParameters(
            order_id=self.order_id,
            ticker=self.ticker,
            volume=self.volume,
            volatility=self.volatility
        )
        
        impact = model.estimate_market_impact(params)
        
        anomaly_detector_mock.detect.assert_called_once_with(self.ticker)
        alert_dispatcher_mock.dispatch.assert_called_once_with(anomaly_dict)
        
        expected_impact = float(self.volume * self.volatility * 0.00005 * multiplier)
        self.assertEqual(impact, expected_impact)

    def test_simulate_stress_slippage(self):
        stress_pipeline_mock = MagicMock()
        stress_multiplier = round(random.uniform(1.5, 5.0), 2)
        stress_pipeline_mock.run_simulation.return_value = {"stress_multiplier": stress_multiplier}
        
        model = MarketPortfolioSlippageModel(stress_scenario_pipeline=stress_pipeline_mock)
        
        result = model.simulate_stress_slippage(self.ticker, self.volume, self.scenario_name)
        
        stress_pipeline_mock.run_simulation.assert_called_once_with(self.scenario_name)
        
        expected_adjusted = round(self.volume * 0.2 * 0.0001 * stress_multiplier, 6)
        self.assertEqual(result["scenario"], self.scenario_name)
        self.assertEqual(result["stress_multiplier"], stress_multiplier)
        self.assertEqual(result["adjusted_slippage"], expected_adjusted)

    def test_simulate_order_execution_buy(self):
        model = MarketPortfolioSlippageModel()
        quantity = random.randint(10, 1000)
        base_price = round(random.uniform(50.0, 500.0), 2)
        adv = 1000000
        volatility = 0.25
        spread_bps = 10.0
        
        order_data = {
            "order_id": self.order_id,
            "symbol": self.ticker,
            "side": "BUY",
            "quantity": quantity,
            "price": base_price
        }
        market_context = {
            "adv": adv,
            "volatility": volatility,
            "spread_bps": spread_bps
        }
        
        res = model.simulate_order_execution(order_data, market_context)
        
        self.assertEqual(res["order_id"], self.order_id)
        self.assertEqual(res["symbol"], self.ticker)
        self.assertEqual(res["side"], "BUY")
        self.assertEqual(res["status"], "FILLED")
        self.assertGreater(res["executed_price"], base_price)

    def test_simulate_order_execution_sell(self):
        model = MarketPortfolioSlippageModel()
        quantity = random.randint(10, 1000)
        base_price = round(random.uniform(50.0, 500.0), 2)
        
        order_data = {
            "order_id": self.order_id,
            "symbol": self.ticker,
            "side": "SELL",
            "quantity": quantity,
            "price": base_price
        }
        market_context = {
            "adv": 500000,
            "volatility": 0.15,
            "spread_bps": 4.0
        }
        
        res = model.simulate_order_execution(order_data, market_context)
        
        self.assertEqual(res["side"], "SELL")
        self.assertLess(res["executed_price"], base_price)

    def test_simulate_batch(self):
        model = MarketPortfolioSlippageModel()
        orders = [
            {"order_id": uuid.uuid4().hex, "symbol": self.ticker, "side": "BUY", "quantity": 100, "price": 100.0}
        ]
        contexts = {
            self.ticker: {"adv": 100000, "volatility": 0.2, "spread_bps": 5.0}
        }
        
        results = model.simulate_batch(orders, contexts)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["symbol"], self.ticker)

    def test_persist_and_get_execution_logs_internal(self):
        storage_mock = MagicMock()
        model = MarketPortfolioSlippageModel(db_storage=storage_mock)
        simulation_id = uuid.uuid4().hex
        executions = [{"id": uuid.uuid4().hex}]
        
        persisted = model.persist_execution_logs(simulation_id, executions, storage_mock)
        self.assertTrue(persisted)
        
        storage_mock.save_logs.assert_called_once_with(simulation_id, executions)
        
        logs = model.get_execution_logs(simulation_id, storage_mock)
        self.assertEqual(logs, executions)

    def test_get_execution_logs_from_storage(self):
        storage_mock = MagicMock()
        simulation_id = uuid.uuid4().hex
        expected_logs = [{"log_id": uuid.uuid4().hex}]
        storage_mock.get_logs.return_value = expected_logs
        
        model = MarketPortfolioSlippageModel()
        logs = model.get_execution_logs(simulation_id, storage_mock)
        
        storage_mock.get_logs.assert_called_once_with(simulation_id)
        self.assertEqual(logs, expected_logs)