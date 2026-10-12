import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)


class TestMarketPortfolioStressAuditSchedulerHubIntegration(unittest.TestCase):

    def test_run_audit_cycle_success(self):
        portfolio_id = str(uuid.uuid4())
        threshold = random.uniform(0.01, 0.99)
        storage_target = str(uuid.uuid4())
        mock_eval_result = {"audit_id": str(uuid.uuid4()), "status": "triggered"}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            instance = MockTriggerClass.return_value
            instance.evaluate_and_trigger.return_value = mock_eval_result

            hub = StressAuditSchedulerHub()
            res = hub.run_audit_cycle(portfolio_id, threshold, storage_target)

            self.assertEqual(res, mock_eval_result)
            instance.evaluate_and_trigger.assert_called_once_with(portfolio_id, threshold)
            mock_vault_process.assert_called_once_with(storage_target, mock_eval_result)

    def test_run_audit_cycle_none_result(self):
        portfolio_id = str(uuid.uuid4())
        threshold = random.uniform(0.01, 0.99)
        storage_target = str(uuid.uuid4())

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            instance = MockTriggerClass.return_value
            instance.evaluate_and_trigger.return_value = None

            hub = StressAuditSchedulerHub()
            res = hub.run_audit_cycle(portfolio_id, threshold, storage_target)

            self.assertIsNone(res)
            instance.evaluate_and_trigger.assert_called_once_with(portfolio_id, threshold)
            mock_vault_process.assert_not_called()

    def test_get_feed_success(self):
        feed_url = f"https://example.com/feed/{uuid.uuid4().hex}"
        expected_bytes = bytes(uuid.uuid4().hex, 'utf-8')

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass:
            instance = MockTriggerClass.return_value
            instance.fetch_external_stress_feed.return_value = expected_bytes

            hub = StressAuditSchedulerHub()
            res = hub.get_feed(feed_url)

            self.assertEqual(res, expected_bytes)
            instance.fetch_external_stress_feed.assert_called_once_with(feed_url)

    def test_get_feed_exception(self):
        feed_url = f"https://example.com/feed/{uuid.uuid4().hex}"

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass:
            instance = MockTriggerClass.return_value
            instance.fetch_external_stress_feed.side_effect = RuntimeError(uuid.uuid4().hex)

            hub = StressAuditSchedulerHub()
            res = hub.get_feed(feed_url)

            self.assertEqual(res, b"")
            instance.fetch_external_stress_feed.assert_called_once_with(feed_url)

    def test_dispatch_alert_and_check_all_success(self):
        audit_id = str(uuid.uuid4())
        message = uuid.uuid4().hex
        storage_target = str(uuid.uuid4())
        export_format = uuid.uuid4().hex

        notification_res = {"status": "sent", "id": audit_id}
        is_valid_res = True
        export_data_res = {"data": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate") as mock_validate, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export") as mock_export:

            instance = MockTriggerClass.return_value
            instance.notify_audit_system.return_value = notification_res
            mock_validate.return_value = is_valid_res
            mock_export.return_value = export_data_res

            hub = StressAuditSchedulerHub()
            result = hub.dispatch_alert_and_check(audit_id, message, storage_target, export_format)

            expected = {
                "notification": notification_res,
                "is_valid": is_valid_res,
                "export_data": export_data_res
            }
            self.assertEqual(result, expected)
            instance.notify_audit_system.assert_called_once_with(audit_id, message)
            mock_validate.assert_called_once_with(storage_target, audit_id)
            mock_export.assert_called_once_with(storage_target, export_format)

    def test_dispatch_alert_and_check_exceptions(self):
        audit_id = str(uuid.uuid4())
        message = uuid.uuid4().hex
        storage_target = str(uuid.uuid4())
        export_format = uuid.uuid4().hex

        notification_res = {"status": "failed"}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate") as mock_validate, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export") as mock_export:

            instance = MockTriggerClass.return_value
            instance.notify_audit_system.return_value = notification_res
            mock_validate.side_effect = ValueError(uuid.uuid4().hex)
            mock_export.side_effect = KeyError(uuid.uuid4().hex)

            hub = StressAuditSchedulerHub()
            result = hub.dispatch_alert_and_check(audit_id, message, storage_target, export_format)

            expected = {
                "notification": notification_res,
                "is_valid": False,
                "export_data": {}
            }
            self.assertEqual(result, expected)

    def test_market_portfolio_stress_audit_scheduler_hub_process(self):
        portfolio_id = str(uuid.uuid4())
        threshold = random.uniform(0.1, 0.9)
        storage_target = str(uuid.uuid4())
        audit_data = {"metric": uuid.uuid4().hex}
        trigger_mock_res = {"evaluated": True}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAuditSchedulerHub.run_audit_cycle") as mock_run_cycle, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            mock_run_cycle.return_value = trigger_mock_res

            res = market_portfolio_stress_audit_scheduler_hub_process(
                portfolio_id, threshold, storage_target, audit_data
            )

            expected = {
                "trigger_result": trigger_mock_res,
                "vault_storage": storage_target
            }
            self.assertEqual(res, expected)
            mock_run_cycle.assert_called_once_with(portfolio_id, threshold, storage_target)
            mock_vault_process.assert_called_once_with(storage_target, audit_data)