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
        self.ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.order_id = uuid.uuid4().hex
        self.volume = round(random.uniform(100.0, 10000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.9), 4)
        self.scenario_name = f"scenario_{uuid.uuid4().hex[:8]}"

    def test_calculate_slippage_success(self):
        market_parser_mock = MagicMock()
        model = MarketPortfolioSlippageModel(market_parser=market_parser_mock)
        params = OrderExecutionParameters(
            order_id=self.order_id,
            ticker=self.ticker,
            volume=self.volume,
            volatility=self.volatility
        )

        result = model.calculate_slippage(params)

        market_parser_mock.parse_market_depth.assert_called_once_with(self.ticker)
        expected = round(self.volume * self.volatility * 0.0001, 6)
        self.assertEqual(result, expected)

    def test_calculate_slippage_invalid_parameters(self):
        audit_notifier_mock = MagicMock()
        model = MarketPortfolioSlippageModel(audit_notifier=audit_notifier_mock)
        
        invalid_volume = -1.0
        params = OrderExecutionParameters(
            order_id=self.order_id,
            ticker=self.ticker,
            volume=invalid_volume,
            volatility=self.volatility
        )

        with self.assertRaises(SlippageCalculationError):
            model.calculate_slippage(params)

        audit_notifier_mock.notify_error.assert_called_once()

    def test_fetch_external_liquidity_profile_success(self):
        api_gateway_mock = MagicMock()
        model = MarketPortfolioSlippageModel(api_gateway=api_gateway_mock)
        random_bytes = uuid.uuid4().bytes

        with patch("skills.market_portfolio_slippage_model.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raw = io.BytesIO(random_bytes)
            mock_get.return_value = mock_response

            result = model.fetch_external_liquidity_profile(self.ticker, self.volume)

            mock_get.assert_called_once()
            api_gateway_mock.log_request.assert_called_once_with(self.ticker, self.volume)
            self.assertEqual(result.read(), random_bytes)

    def test_fetch_external_liquidity_profile_exception(self):
        api_gateway_mock = MagicMock()
        model = MarketPortfolioSlippageModel(api_gateway=api_gateway_mock)

        with patch("skills.market_portfolio_slippage_model.requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Network failure")

            result = model.fetch_external_liquidity_profile(self.ticker, self.volume)

            api_gateway_mock.log_request.assert_called_once_with(self.ticker, self.volume)
            self.assertIsNone(result)

    def test_estimate_market_impact_with_anomaly(self):
        anomaly_detector_mock = MagicMock()
        alert_dispatcher_mock = MagicMock()
        multiplier = round(random.uniform(1.5, 5.0), 2)
        anomaly_data = {"multiplier": multiplier, "uid": uuid.uuid4().hex}
        anomaly_detector_mock.detect.return_value = anomaly_data

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
        alert_dispatcher_mock.dispatch.assert_called_once_with(anomaly_data)
        expected = float(self.volume * self.volatility * 0.00005 * multiplier)
        self.assertEqual(impact, expected)

    def test_simulate_stress_slippage(self):
        stress_pipeline_mock = MagicMock()
        stress_multiplier = round(random.uniform(2.0, 10.0), 2)
        stress_pipeline_mock.run_simulation.return_value = {"stress_multiplier": stress_multiplier}

        model = MarketPortfolioSlippageModel(stress_scenario_pipeline=stress_pipeline_mock)

        result = model.simulate_stress_slippage(self.ticker, self.volume, self.scenario_name)

        stress_pipeline_mock.run_simulation.assert_called_once_with(self.scenario_name)
        self.assertEqual(result["scenario"], self.scenario_name)
        self.assertEqual(result["stress_multiplier"], stress_multiplier)
        expected_slippage = round(self.volume * 0.2 * 0.0001 * stress_multiplier, 6)
        self.assertEqual(result["adjusted_slippage"], expected_slippage)

    def test_simulate_order_execution_buy(self):
        model = MarketPortfolioSlippageModel()
        price = round(random.uniform(50.0, 500.0), 2)
        quantity = round(random.uniform(100, 1000), 2)
        order_data = {
            "order_id": self.order_id,
            "symbol": self.ticker,
            "side": "BUY",
            "quantity": quantity,
            "price": price
        }
        market_context = {
            "adv": 50000.0,
            "volatility": self.volatility,
            "spread_bps": 10.0
        }

        result = model.simulate_order_execution(order_data, market_context)

        self.assertEqual(result["order_id"], self.order_id)
        self.assertEqual(result["symbol"], self.ticker)
        self.assertEqual(result["side"], "BUY")
        self.assertEqual(result["status"], "FILLED")
        self.assertGreater(result["executed_price"], price)

    def test_simulate_batch(self):
        model = MarketPortfolioSlippageModel()
        order_list = [
            {
                "order_id": uuid.uuid4().hex,
                "symbol": self.ticker,
                "side": random.choice(["BUY", "SELL"]),
                "quantity": 200.0,
                "price": 150.0
            }
        ]
        contexts = {
            self.ticker: {"adv": 10000.0, "volatility": 0.15, "spread_bps": 4.0}
        }

        results = model.simulate_batch(order_list, contexts)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["symbol"], self.ticker)
        self.assertEqual(results[0]["status"], "FILLED")

    def test_persist_and_get_execution_logs(self):
        storage_mock = MagicMock()
        model = MarketPortfolioSlippageModel()
        simulation_id = uuid.uuid4().hex
        executions = [{"id": uuid.uuid4().hex, "cost": 123.45}]

        persisted = model.persist_execution_logs(simulation_id, executions, storage_mock)
        self.assertTrue(persisted)
        storage_mock.save_logs.assert_called_once_with(simulation_id, executions)

        logs = model.get_execution_logs(simulation_id, storage_mock)
        self.assertEqual(logs, executions)

    def test_get_execution_logs_from_storage(self):
        storage_mock = MagicMock()
        simulation_id = uuid.uuid4().hex
        expected_logs = [{"id": uuid.uuid4().hex}]
        storage_mock.get_logs.return_value = expected_logs

        model = MarketPortfolioSlippageModel()
        logs = model.get_execution_logs(simulation_id, storage_mock)

        storage_mock.get_logs.assert_called_once_with(simulation_id)
        self.assertEqual(logs, expected_logs)


if __name__ == "__main__":
    unittest.main()