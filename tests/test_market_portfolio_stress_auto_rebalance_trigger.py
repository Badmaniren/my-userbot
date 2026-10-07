import unittest
from unittest.mock import patch, MagicMock
import random
import uuid

try:
    import requests
except ImportError:
    requests = MagicMock()

from skills.market_portfolio_stress_auto_rebalance_trigger import StressAutoRebalanceTrigger, _GlobalModuleProxy

class TestStressAutoRebalanceTrigger(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.threshold = round(random.uniform(0.1, 0.9), 4)
        self.url = f"https://{uuid.uuid4().hex}.com/feed"
        self.alert_id = uuid.uuid4().hex
        self.message = uuid.uuid4().hex

    def test_evaluate_and_trigger_with_explicit_threshold_and_high_stress(self):
        mock_simulator = MagicMock()
        stress_score = self.threshold + 0.1
        mock_simulator.run_simulation.return_value = {
            "stress_score": stress_score,
            "critical_threshold": self.threshold
        }

        expected_signal = {"signal": uuid.uuid4().hex, "status": uuid.uuid4().hex}
        mock_optimizer = MagicMock()
        mock_optimizer.generate_rebalance_signal.return_value = expected_signal

        trigger = StressAutoRebalanceTrigger(
            market_portfolio_scenario_simulator=mock_simulator,
            market_portfolio_strategy_optimizer=mock_optimizer
        )

        result = trigger.evaluate_and_trigger(self.portfolio_id, threshold=self.threshold)
        self.assertEqual(result, expected_signal)
        mock_optimizer.generate_rebalance_signal.assert_called_once()

    def test_evaluate_and_trigger_fallback_no_threshold(self):
        mock_simulator = MagicMock()
        mock_simulator.run_simulation.return_value = {}
        mock_db = MagicMock()

        trigger = StressAutoRebalanceTrigger(
            market_portfolio_scenario_simulator=mock_simulator,
            db_storage=mock_db
        )

        result = trigger.evaluate_and_trigger(self.portfolio_id, threshold=None)
        self.assertIsNotNone(result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["status"], "TRIGGERED")
        mock_db.save.assert_called_once()

    def test_execute_rebalance_success(self):
        mock_db = MagicMock()
        trigger = StressAutoRebalanceTrigger(db_storage=mock_db)
        hedges = [{"asset": "BTC", "amount": 1.0}]
        weights = {"BTC": 0.5, "ETH": 0.5}

        result = trigger.execute_rebalance(self.portfolio_id, hedges=hedges, weights=weights)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["status"], "EXECUTED")
        self.assertEqual(result["hedges"], hedges)
        self.assertEqual(result["weights"], weights)
        mock_db.save.assert_called_once()

    def test_fetch_external_stress_feed_success(self):
        random_bytes = uuid.uuid4().bytes
        trigger = StressAutoRebalanceTrigger()

        with patch("skills.market_portfolio_stress_auto_rebalance_trigger.requests") as mock_requests:
            if mock_requests is None:
                mock_requests = MagicMock()
            mock_response = MagicMock()
            mock_response.content = random_bytes
            mock_requests.get.return_value = mock_response

            content = trigger.fetch_external_stress_feed(self.url)
            self.assertEqual(content, random_bytes)

    def test_fetch_external_stress_feed_http_error(self):
        trigger = StressAutoRebalanceTrigger()
        with patch("skills.market_portfolio_stress_auto_rebalance_trigger.requests") as mock_requests:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = RuntimeError("404 Not Found")
            mock_requests.get.return_value = mock_response

            with self.assertRaises(Exception):
                trigger.fetch_external_stress_feed(self.url)

    def test_notify_audit_system_with_bool_return(self):
        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch.return_value = True

        trigger = StressAutoRebalanceTrigger(
            market_portfolio_alert_dispatcher=mock_dispatcher
        )

        result = trigger.notify_audit_system(self.alert_id, self.message)
        expected = {"alert_id": self.alert_id, "dispatched": True}
        self.assertEqual(result, expected)
        mock_dispatcher.dispatch.assert_called_once_with({
            "alert_id": self.alert_id,
            "message": self.message
        })

    def test_notify_audit_system_with_dict_return(self):
        mock_dispatcher = MagicMock()
        expected = {"alert_id": self.alert_id, "status": "SENT"}
        mock_dispatcher.dispatch.return_value = expected

        trigger = StressAutoRebalanceTrigger(
            market_portfolio_alert_dispatcher=mock_dispatcher
        )

        result = trigger.notify_audit_system(self.alert_id, self.message)
        self.assertEqual(result, expected)

    def test_global_proxy_delegation(self):
        proxy = _GlobalModuleProxy()
        random_bytes = uuid.uuid4().bytes

        with patch("skills.market_portfolio_stress_auto_rebalance_trigger.requests") as mock_requests:
            mock_response = MagicMock()
            mock_response.content = random_bytes
            mock_requests.get.return_value = mock_response

            content = proxy.fetch_external_stress_feed(self.url)
            self.assertEqual(content, random_bytes)

        # Test __call__ with portfolio_id
        res_call = proxy(self.portfolio_id)
        self.assertIsNotNone(res_call)

    def test_evaluate_and_trigger_low_stress_returns_none(self):
        mock_simulator = MagicMock()
        stress_score = self.threshold - 0.1
        mock_simulator.run_simulation.return_value = {
            "stress_score": stress_score,
            "critical_threshold": self.threshold
        }

        trigger = StressAutoRebalanceTrigger(
            market_portfolio_scenario_simulator=mock_simulator
        )

        result = trigger.evaluate_and_trigger(self.portfolio_id, threshold=self.threshold)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
