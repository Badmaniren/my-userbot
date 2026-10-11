import unittest
from unittest.mock import patch
import random
import uuid
import io

from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)


class TestStressAuditSchedulerHub(unittest.TestCase):

    def test_run_audit_cycle_success(self):
        portfolio_id = uuid.uuid4().hex
        threshold = random.uniform(1.0, 100.0)
        storage_target = uuid.uuid4().hex
        expected_eval_result = {"status": uuid.uuid4().hex, "metric": random.randint(1, 1000)}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger.evaluate_and_trigger", return_value=expected_eval_result) as mock_eval, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            hub = StressAuditSchedulerHub()
            res = hub.run_audit_cycle(portfolio_id, threshold, storage_target)

            mock_eval.assert_called_once_with(portfolio_id, threshold)
            mock_vault_process.assert_called_once_with(storage_target, expected_eval_result)
            self.assertEqual(res, expected_eval_result)

    def test_run_audit_cycle_none_result(self):
        portfolio_id = uuid.uuid4().hex
        threshold = random.uniform(1.0, 100.0)
        storage_target = uuid.uuid4().hex

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger.evaluate_and_trigger", return_value=None) as mock_eval, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            hub = StressAuditSchedulerHub()
            res = hub.run_audit_cycle(portfolio_id, threshold, storage_target)

            mock_eval.assert_called_once_with(portfolio_id, threshold)
            mock_vault_process.assert_not_called()
            self.assertIsNone(res)

    def test_get_feed_success(self):
        feed_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        expected_bytes = uuid.uuid4().hex.encode('utf-8')

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger.fetch_external_stress_feed", return_value=expected_bytes) as mock_fetch:
            hub = StressAuditSchedulerHub()
            res = hub.get_feed(feed_url)

            mock_fetch.assert_called_once_with(feed_url)
            self.assertEqual(res, expected_bytes)

    def test_get_feed_exception_returns_empty_bytes(self):
        feed_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger.fetch_external_stress_feed", side_effect=Exception(uuid.uuid4().hex)) as mock_fetch:
            hub = StressAuditSchedulerHub()
            res = hub.get_feed(feed_url)

            mock_fetch.assert_called_once_with(feed_url)
            self.assertEqual(res, b"")

    def test_dispatch_alert_and_check_all_success(self):
        audit_id = uuid.uuid4().hex
        message = uuid.uuid4().hex
        storage_target = uuid.uuid4().hex
        export_format = uuid.uuid4().hex

        expected_notification = uuid.uuid4().hex
        expected_is_valid = random.choice([True, False])
        expected_export_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger.notify_audit_system", return_value=expected_notification) as mock_notify, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate", return_value=expected_is_valid) as mock_validate, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export", return_value=expected_export_data) as mock_export:

            hub = StressAuditSchedulerHub()
            res = hub.dispatch_alert_and_check(audit_id, message, storage_target, export_format)

            mock_notify.assert_called_once_with(audit_id, message)
            mock_validate.assert_called_once_with(storage_target, audit_id)
            mock_export.assert_called_once_with(storage_target, export_format)

            self.assertEqual(res["notification"], expected_notification)
            self.assertEqual(res["is_valid"], expected_is_valid)
            self.assertEqual(res["export_data"], expected_export_data)

    def test_dispatch_alert_and_check_exceptions_handled(self):
        audit_id = uuid.uuid4().hex
        message = uuid.uuid4().hex
        storage_target = uuid.uuid4().hex
        export_format = uuid.uuid4().hex

        expected_notification = uuid.uuid4().hex

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger.notify_audit_system", return_value=expected_notification) as mock_notify, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate", side_effect=Exception(uuid.uuid4().hex)) as mock_validate, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export", side_effect=Exception(uuid.uuid4().hex)) as mock_export:

            hub = StressAuditSchedulerHub()
            res = hub.dispatch_alert_and_check(audit_id, message, storage_target, export_format)

            mock_notify.assert_called_once_with(audit_id, message)
            mock_validate.assert_called_once_with(storage_target, audit_id)
            mock_export.assert_called_once_with(storage_target, export_format)

            self.assertEqual(res["notification"], expected_notification)
            self.assertFalse(res["is_valid"])
            self.assertEqual(res["export_data"], {})

    def test_market_portfolio_stress_audit_scheduler_hub_process(self):
        portfolio_id = uuid.uuid4().hex
        threshold = random.uniform(1.0, 100.0)
        storage_target = uuid.uuid4().hex
        audit_data = {uuid.uuid4().hex: random.randint(10, 500)}

        expected_trigger_res = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAuditSchedulerHub.run_audit_cycle", return_value=expected_trigger_res) as mock_run_cycle, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            res = market_portfolio_stress_audit_scheduler_hub_process(portfolio_id, threshold, storage_target, audit_data)

            mock_run_cycle.assert_called_once_with(portfolio_id, threshold, storage_target)
            mock_vault_process.assert_called_once_with(storage_target, audit_data)

            self.assertEqual(res["trigger_result"], expected_trigger_res)
            self.assertEqual(res["vault_storage"], storage_target)