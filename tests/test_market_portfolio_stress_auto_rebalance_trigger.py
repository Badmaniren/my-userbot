import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.market_portfolio_stress_auto_rebalance_trigger import (
    StressAutoRebalanceTrigger,
    market_portfolio_stress_auto_rebalance_trigger
)

class TestStressAutoRebalanceTrigger(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.threshold = round(random.uniform(0.1, 0.9), 4)
        self.stress_score = round(random.uniform(self.threshold + 0.01, 1.0), 4)
        self.alert_id = uuid.uuid4().hex
        self.message = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self.url = f"https://{uuid.uuid4().hex}.com/feed"
        self.feed_content = uuid.uuid4().bytes

    def test_evaluate_and_trigger_above_threshold(self):
        mock_simulator = MagicMock()
        mock_simulator.run_simulation.return_value = {
            "stress_score": self.stress_score,
            "critical_threshold": self.threshold
        }

        expected_signal = {
            "portfolio_id": self.portfolio_id,
            "status": "REBALANCED",
            "signal_id": uuid.uuid4().hex
        }
        mock_optimizer = MagicMock()
        mock_optimizer.generate_rebalance_signal.return_value = expected_signal

        trigger = StressAutoRebalanceTrigger(
            market_portfolio_scenario_simulator=mock_simulator,
            market_portfolio_strategy_optimizer=mock_optimizer
        )

        result = trigger.evaluate_and_trigger(self.portfolio_id, self.threshold)
        self.assertEqual(result, expected_signal)
        mock_simulator.run_simulation.assert_called_once_with(portfolio_id=self.portfolio_id, threshold=self.threshold)
        mock_optimizer.generate_rebalance_signal.assert_called_once()

    def test_evaluate_and_trigger_no_threshold_fallback(self):
        mock_simulator = MagicMock()
        mock_simulator.run_simulation.return_value = {}

        mock_db = MagicMock()

        trigger = StressAutoRebalanceTrigger(
            db_storage=mock_db,
            market_portfolio_scenario_simulator=mock_simulator
        )

        result = trigger.evaluate_and_trigger(self.portfolio_id, threshold=None)
        self.assertIsNotNone(result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["status"], "TRIGGERED")
        self.assertTrue(result["logged"])
        mock_db.save.assert_called_once()

    def test_fetch_external_stress_feed(self):
        trigger = StressAutoRebalanceTrigger()

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = self.feed_content
            mock_get.return_value = mock_response

            content = trigger.fetch_external_stress_feed(self.url)
            self.assertEqual(content, self.feed_content)
            mock_get.assert_called_once_with(self.url)

    def test_notify_audit_system_bool_response(self):
        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch.return_value = True

        trigger = StressAutoRebalanceTrigger(
            market_portfolio_alert_dispatcher=mock_dispatcher
        )

        result = trigger.notify_audit_system(self.alert_id, self.message)
        self.assertEqual(result, {"alert_id": self.alert_id, "dispatched": True})
        mock_dispatcher.dispatch.assert_called_once_with({
            "alert_id": self.alert_id,
            "message": self.message
        })

    def test_notify_audit_system_dict_response(self):
        mock_dispatcher = MagicMock()
        expected_dict = {"alert_id": self.alert_id, "dispatched": True, "custom_field": uuid.uuid4().hex}
        mock_dispatcher.dispatch.return_value = expected_dict

        trigger = StressAutoRebalanceTrigger(
            market_portfolio_alert_dispatcher=mock_dispatcher
        )

        result = trigger.notify_audit_system(self.alert_id, self.message)
        self.assertEqual(result, expected_dict)

    def test_global_module_proxy_integration(self):
        with patch("skills.market_portfolio_stress_auto_rebalance_trigger.StressAutoRebalanceTrigger.fetch_external_stress_feed") as mock_fetch:
            mock_fetch.return_value = self.feed_content
            res = market_portfolio_stress_auto_rebalance_trigger.fetch_external_stress_feed(self.url)
            self.assertEqual(res, self.feed_content)
            mock_fetch.assert_called_once_with(self.url)

if __name__ == "__main__":
    unittest.main()