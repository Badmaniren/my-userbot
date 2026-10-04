import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import requests

from skills.market_portfolio_stress_auto_rebalance_trigger import (
    StressAutoRebalanceTrigger,
    market_portfolio_stress_auto_rebalance_trigger
)

class TestMarketPortfolioStressAutoRebalanceTrigger(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.threshold = round(random.uniform(0.1, 0.9), 4)
        self.trigger = StressAutoRebalanceTrigger()

    def test_evaluate_and_trigger_no_threshold_empty_sim(self):
        mock_sim = MagicMock()
        mock_sim.run_simulation.return_value = {}
        mock_db = MagicMock()

        trigger = StressAutoRebalanceTrigger(
            market_portfolio_scenario_simulator=mock_sim,
            db_storage=mock_db
        )

        res = trigger.evaluate_and_trigger(self.portfolio_id, threshold=None)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(res.get("status"), "TRIGGERED")
        self.assertTrue(res.get("logged"))
        mock_db.save.assert_called_once()

    def test_evaluate_and_trigger_exceeds_threshold(self):
        mock_sim = MagicMock()
        stress_score = self.threshold + 0.1
        mock_sim.run_simulation.return_value = {
            "stress_score": stress_score,
            "critical_threshold": self.threshold
        }

        expected_signal = {
            "signal_id": uuid.uuid4().hex,
            "action": "REBALANCE_NOW",
            "score": stress_score
        }
        mock_optimizer = MagicMock()
        mock_optimizer.generate_rebalance_signal.return_value = expected_signal

        trigger = StressAutoRebalanceTrigger(
            market_portfolio_scenario_simulator=mock_sim,
            market_portfolio_strategy_optimizer=mock_optimizer
        )

        res = trigger.evaluate_and_trigger(self.portfolio_id, threshold=self.threshold)
        self.assertEqual(res, expected_signal)
        mock_optimizer.generate_rebalance_signal.assert_called_once()

    def test_evaluate_and_trigger_below_threshold(self):
        mock_sim = MagicMock()
        stress_score = self.threshold - 0.1
        mock_sim.run_simulation.return_value = {
            "stress_score": stress_score,
            "critical_threshold": self.threshold
        }

        mock_optimizer = MagicMock()

        trigger = StressAutoRebalanceTrigger(
            market_portfolio_scenario_simulator=mock_sim,
            market_portfolio_strategy_optimizer=mock_optimizer
        )

        res = trigger.evaluate_and_trigger(self.portfolio_id, threshold=self.threshold)
        self.assertIsNone(res)
        mock_optimizer.generate_rebalance_signal.assert_not_called()

    def test_evaluate_and_trigger_fallback_with_sim_result(self):
        mock_sim = MagicMock()
        mock_sim.run_simulation.return_value = {
            "stress_score": 0.05,
            "critical_threshold": 0.5
        }
        mock_db = MagicMock()

        trigger = StressAutoRebalanceTrigger(
            market_portfolio_scenario_simulator=mock_sim,
            db_storage=mock_db
        )

        res = trigger.evaluate_and_trigger(self.portfolio_id, threshold=None)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "TRIGGERED")
        mock_db.save.assert_called_once()

    def test_fetch_external_stress_feed(self):
        random_url = f"https://{uuid.uuid4().hex}.com/feed"
        random_content = uuid.uuid4().bytes

        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.content = random_content
            mock_get.return_value = mock_resp

            content = self.trigger.fetch_external_stress_feed(random_url)
            self.assertEqual(content, random_content)
            mock_get.assert_called_once_with(random_url)

    def test_notify_audit_system_bool_response(self):
        alert_id = uuid.uuid4().hex
        message = uuid.uuid4().hex
        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch.return_value = True

        trigger = StressAutoRebalanceTrigger(market_portfolio_alert_dispatcher=mock_dispatcher)
        res = trigger.notify_audit_system(alert_id, message)

        self.assertEqual(res, {"alert_id": alert_id, "dispatched": True})
        mock_dispatcher.dispatch.assert_called_once_with({
            "alert_id": alert_id,
            "message": message
        })

    def test_notify_audit_system_dict_response(self):
        alert_id = uuid.uuid4().hex
        message = uuid.uuid4().hex
        expected_dict = {"alert_id": alert_id, "dispatched": True, "custom": uuid.uuid4().hex}
        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch.return_value = expected_dict

        trigger = StressAutoRebalanceTrigger(market_portfolio_alert_dispatcher=mock_dispatcher)
        res = trigger.notify_audit_system(alert_id, message)

        self.assertEqual(res, expected_dict)

    def test_notify_audit_system_no_dispatcher(self):
        alert_id = uuid.uuid4().hex
        message = uuid.uuid4().hex

        trigger = StressAutoRebalanceTrigger(market_portfolio_alert_dispatcher=None)
        res = trigger.notify_audit_system(alert_id, message)
        self.assertEqual(res, {"alert_id": alert_id, "dispatched": False})

    def test_global_module_proxy(self):
        with patch("skills.market_portfolio_stress_auto_rebalance_trigger.StressAutoRebalanceTrigger.evaluate_and_trigger") as mock_eval:
            rand_res = {"id": uuid.uuid4().hex}
            mock_eval.return_value = rand_res

            res = market_portfolio_stress_auto_rebalance_trigger.evaluate_and_trigger(self.portfolio_id, self.threshold)
            self.assertEqual(res, rand_res)
            mock_eval.assert_called_once_with(self.portfolio_id, self.threshold)