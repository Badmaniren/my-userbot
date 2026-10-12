import unittest
from unittest.mock import patch
import os
import uuid
import random

from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)


class TestMarketPortfolioStressAuditSchedulerHubIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.threshold = round(random.uniform(0.01, 0.99), 4)
        self.storage_target = f"test_target_{uuid.uuid4().hex}.json"
        self.audit_id = uuid.uuid4().hex
        self.message = uuid.uuid4().hex
        self.export_format = random.choice(["json", "csv", "xml"])
        self.feed_url = f"https://{uuid.uuid4().hex}.com/feed"
        self.audit_data = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}

    def tearDown(self):
        if os.path.exists(self.storage_target):
            try:
                os.remove(self.storage_target)
            except OSError:
                pass

    def test_run_audit_cycle_success(self):
        hub = StressAuditSchedulerHub()
        mock_eval_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_auto_rebalance_trigger.StressAutoRebalanceTrigger.evaluate_and_trigger", return_value=mock_eval_result) as mock_eval, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            res = hub.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

            mock_eval.assert_called_once_with(self.portfolio_id, self.threshold)
            mock_vault_process.assert_called_once_with(self.storage_target, mock_eval_result)
            self.assertEqual(res, mock_eval_result)

    def test_run_audit_cycle_none_result(self):
        hub = StressAuditSchedulerHub()

        with patch("skills.market_portfolio_stress_auto_rebalance_trigger.StressAutoRebalanceTrigger.evaluate_and_trigger", return_value=None) as mock_eval, \
             patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            res = hub.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

            mock_eval.assert_called_once_with(self.portfolio_id, self.threshold)
            mock_vault_process.assert_not_called()
            self.assertIsNone(res)

    def test_get_feed_success(self):
        hub = StressAuditSchedulerHub()
        expected_bytes = uuid.uuid4().hex.encode("utf-8")

        with patch("skills.market_portfolio_stress_auto_rebalance_trigger.StressAutoRebalanceTrigger.fetch_external_stress_feed", return_value=expected_bytes) as mock_fetch:
            res = hub.get_feed(self.feed_url)
            mock_fetch.assert_called_once_with(self.feed_url)
            self.assertEqual(res, expected_bytes)

    def test_get_feed_exception(self):
        hub = StressAuditSchedulerHub()

        with patch("skills.market_portfolio_stress_auto_rebalance_trigger.StressAutoRebalanceTrigger.fetch_external_stress_feed", side_effect=Exception(uuid.uuid4().hex)) as mock_fetch:
            res = hub.get_feed(self.feed_url)
            mock_fetch.assert_called_once_with(self.feed_url)
            self.assertEqual(res, b"")

    def test_dispatch_alert_and_check_success(self):
        hub = StressAuditSchedulerHub()
        notif_res = {uuid.uuid4().hex: uuid.uuid4().hex}
        is_valid_res = random.choice([True, False])
        export_data_res = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_auto_rebalance_trigger.StressAutoRebalanceTrigger.notify_audit_system", return_value=notif_res) as mock_notify, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate", return_value=is_valid_res) as mock_validate, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export", return_value=export_data_res) as mock_export:

            res = hub.dispatch_alert_and_check(self.audit_id, self.message, self.storage_target, self.export_format)

            mock_notify.assert_called_once_with(self.audit_id, self.message)
            mock_validate.assert_called_once_with(self.storage_target, self.audit_id)
            mock_export.assert_called_once_with(self.storage_target, self.export_format)

            self.assertEqual(res["notification"], notif_res)
            self.assertEqual(res["is_valid"], is_valid_res)
            self.assertEqual(res["export_data"], export_data_res)

    def test_dispatch_alert_and_check_exceptions(self):
        hub = StressAuditSchedulerHub()
        notif_res = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_auto_rebalance_trigger.StressAutoRebalanceTrigger.notify_audit_system", return_value=notif_res), \
             patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_validate", side_effect=Exception(uuid.uuid4().hex)), \
             patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_export", side_effect=Exception(uuid.uuid4().hex)):

            res = hub.dispatch_alert_and_check(self.audit_id, self.message, self.storage_target, self.export_format)

            self.assertEqual(res["notification"], notif_res)
            self.assertFalse(res["is_valid"])
            self.assertEqual(res["export_data"], {})

    def test_market_portfolio_stress_audit_scheduler_hub_process(self):
        mock_trigger_res = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAuditSchedulerHub.run_audit_cycle", return_value=mock_trigger_res) as mock_run_cycle, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            result = market_portfolio_stress_audit_scheduler_hub_process(
                self.portfolio_id, self.threshold, self.storage_target, self.audit_data
            )

            mock_run_cycle.assert_called_once_with(self.portfolio_id, self.threshold, self.storage_target)
            mock_vault_process.assert_called_once_with(self.storage_target, self.audit_data)

            self.assertEqual(result["trigger_result"], mock_trigger_res)
            self.assertEqual(result["vault_storage"], self.storage_target)


if __name__ == "__main__":
    unittest.main()