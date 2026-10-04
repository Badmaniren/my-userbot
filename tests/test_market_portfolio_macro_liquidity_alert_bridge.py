import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.market_portfolio_macro_liquidity_alert_bridge import (
    MarketPortfolioMacroLiquidityAlertBridge,
    market_portfolio_macro_liquidity_alert_bridge
)

class TestMarketPortfolioMacroLiquidityAlertBridge(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.external_url = f"https://{uuid.uuid4().hex}.com/stream"
        self.mock_db = MagicMock()
        self.mock_analyzer = MagicMock()
        self.mock_monitor = MagicMock()
        self.mock_dispatcher = MagicMock()

        self.bridge = MarketPortfolioMacroLiquidityAlertBridge(
            db_storage=self.mock_db,
            market_portfolio_liquidity_scenario_analyzer=self.mock_analyzer,
            market_portfolio_monitor=self.mock_monitor,
            market_portfolio_alert_dispatcher=self.mock_dispatcher
        )

    def test_factory_function(self):
        bridge_instance = market_portfolio_macro_liquidity_alert_bridge()
        self.assertIsInstance(bridge_instance, MarketPortfolioMacroLiquidityAlertBridge)

    def test_process_macro_liquidity_alerts_triggered(self):
        scenario_name = uuid.uuid4().hex
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        message = uuid.uuid4().hex

        liquidity_payload = {"liquidity_score": random.random()}
        self.mock_monitor.get_portfolio_liquidity.return_value = liquidity_payload
        self.mock_analyzer.evaluate_scenario.return_value = {
            "triggered": True,
            "severity": severity,
            "scenario": scenario_name,
            "message": message
        }

        result = self.bridge.process_macro_liquidity_alerts(self.portfolio_id)

        self.assertTrue(result.get("alert_dispatched"))
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("alert_id", result)

        self.mock_monitor.get_portfolio_liquidity.assert_called_once_with(self.portfolio_id)
        self.mock_analyzer.evaluate_scenario.assert_called_once_with(liquidity_payload)
        self.mock_db.save_alert.assert_called_once()
        self.mock_dispatcher.dispatch.assert_called_once()

        dispatched_arg = self.mock_dispatcher.dispatch.call_args[0][0]
        self.assertEqual(dispatched_arg["portfolio_id"], self.portfolio_id)
        self.assertEqual(dispatched_arg["severity"], severity)
        self.assertEqual(dispatched_arg["message"], message)

    def test_process_macro_liquidity_alerts_not_triggered(self):
        self.mock_monitor.get_portfolio_liquidity.return_value = {}
        self.mock_analyzer.evaluate_scenario.return_value = {"triggered": False}

        result = self.bridge.process_macro_liquidity_alerts(self.portfolio_id)

        self.assertFalse(result.get("alert_dispatched"))
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.mock_db.save_alert.assert_not_called()
        self.mock_dispatcher.dispatch.assert_not_called()

    def test_process_macro_liquidity_alerts_exception_handling(self):
        error_msg = uuid.uuid4().hex
        self.mock_monitor.get_portfolio_liquidity.side_effect = Exception(error_msg)

        result = self.bridge.process_macro_liquidity_alerts(self.portfolio_id)

        self.assertFalse(result.get("success", True))
        self.assertEqual(result.get("error"), error_msg)
        self.assertIn("error_id", result)
        self.mock_db.log_error.assert_called_once()

        logged_error = self.mock_db.log_error.call_args[0][0]
        self.assertEqual(logged_error["portfolio_id"], self.portfolio_id)
        self.assertEqual(logged_error["error"], error_msg)

    def test_ingest_external_macro_stream(self):
        random_bytes = uuid.uuid4().hex.encode('utf-8')
        mock_response = MagicMock()
        mock_response.raw = io.BytesIO(random_bytes)

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = self.bridge.ingest_external_macro_stream(self.external_url, self.portfolio_id)
            mock_get.assert_called_once_with(self.external_url, stream=True)

        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("stream_hash", result)
        self.assertEqual(len(result.get("stream_hash")), 64)

    def test_batch_process_portfolios(self):
        pids = [uuid.uuid4().hex, uuid.uuid4().hex, uuid.uuid4().hex]

        self.mock_monitor.get_portfolio_liquidity.return_value = {}
        self.mock_analyzer.evaluate_scenario.return_value = {"triggered": False}

        results = self.bridge.batch_process_portfolios(pids)

        self.assertEqual(len(results), len(pids))
        for idx, pid in enumerate(pids):
            self.assertEqual(results[idx]["portfolio_id"], pid)
            self.assertFalse(results[idx]["alert_dispatched"])

    def test_generate_and_route_alert(self):
        alert_id = uuid.uuid4().hex
        correlation_id = uuid.uuid4().hex
        bridge_input = {
            "portfolio_id": self.portfolio_id,
            "alert_id": alert_id,
            "correlation_id": correlation_id
        }

        result = self.bridge.generate_and_route_alert(bridge_input)

        self.assertEqual(result.get("alert_status"), "routed")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("alert_id"), alert_id)
        self.assertEqual(result.get("correlation_id"), correlation_id)