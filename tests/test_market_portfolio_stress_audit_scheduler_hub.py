import unittest
from unittest.mock import patch
import uuid
import random
import io

from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)


class TestStressAuditSchedulerHub(unittest.TestCase):

    def test_run_audit_cycle_with_result(self):
        portfolio_id = uuid.uuid4().hex
        threshold = random.uniform(1.0, 100.0)
        storage_target = uuid.uuid4().hex
        expected_res = {"status": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as mock_trigger_cls, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:
            
            mock_trigger_instance = mock_trigger_cls.return_value
            mock_trigger_instance.evaluate_and_trigger.return_value = expected_res

            hub = StressAuditSchedulerHub()
            res = hub.run_audit_cycle(portfolio_id, threshold, storage_target)

            self.assertEqual(res, expected_res)
            mock_trigger_instance.evaluate_and_trigger.assert_called_once_with(portfolio_id, threshold)
            mock_vault_process.assert_called_once_with(storage_target, expected_res)

    def test_run_audit_cycle_with_none(self):
        portfolio_id = uuid.uuid4().hex
        threshold = random.uniform(1.0, 100.0)
        storage_target = uuid.uuid4().hex

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as mock_trigger_cls, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:
            
            mock_trigger_instance = mock_trigger_cls.return_value
            mock_trigger_instance.evaluate_and_trigger.return_value = None

            hub = StressAuditSchedulerHub()
            res = hub.run_audit_cycle(portfolio_id, threshold, storage_target)

            self.assertIsNone(res)
            mock_trigger_instance.evaluate_and_trigger.assert_called_once_with(portfolio_id, threshold)
            mock_vault_process.assert_not_called()

    def test_get_feed_success(self):
        feed_url = f"https://{uuid.uuid4().hex}.com/feed"
        expected_bytes = uuid.uuid4().bytes

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as mock_trigger_cls:
            mock_trigger_instance = mock_trigger_cls.return_value
            mock_trigger_instance.fetch_external_stress_feed.return_value = expected_bytes

            hub = StressAuditSchedulerHub()
            res = hub.get_feed(feed_url)

            self.assertEqual(res, expected_bytes)
            mock_trigger_instance.fetch_external_stress_feed.assert_called_once_with(feed_url)

    def test_get_feed_exception(self):
        feed_url = f"https://{uuid.uuid4().hex}.com/feed"

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as mock_trigger_cls:
            mock_trigger_instance = mock_trigger_cls.return_value
            mock_trigger_instance.fetch_external_stress_feed.side_effect = Exception(uuid.uuid4().hex)

            hub = StressAuditSchedulerHub()
            res = hub.get_feed(feed_url)

            self.assertEqual(res, b"")
            mock_trigger_instance.fetch_external_stress_feed.assert_called_once_with(feed_url)

    def test_dispatch_alert_and_check_success(self):
        audit_id = uuid.uuid4().hex
        message = uuid.uuid4().hex
        storage_target = uuid.uuid4().hex
        export_format = uuid.uuid4().hex

        notification_res = {"notify": uuid.uuid4().hex}
        expected_export = {"data": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as mock_trigger_cls, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate") as mock_validate, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export") as mock_export:
            
            mock_trigger_instance = mock_trigger_cls.return_value
            mock_trigger_instance.notify_audit_system.return_value = notification_res
            mock_validate.return_value = True
            mock_export.return_value = expected_export

            hub = StressAuditSchedulerHub()
            res = hub.dispatch_alert_and_check(audit_id, message, storage_target, export_format)

            expected_dict = {
                "notification": notification_res,
                "is_valid": True,
                "export_data": expected_export
            }
            self.assertEqual(res, expected_dict)
            mock_trigger_instance.notify_audit_system.assert_called_once_with(audit_id, message)
            mock_validate.assert_called_once_with(storage_target, audit_id)
            mock_export.assert_called_once_with(storage_target, export_format)

    def test_dispatch_alert_and_check_exceptions(self):
        audit_id = uuid.uuid4().hex
        message = uuid.uuid4().hex
        storage_target = uuid.uuid4().hex
        export_format = uuid.uuid4().hex

        notification_res = uuid.uuid4().hex

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as mock_trigger_cls, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate") as mock_validate, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export") as mock_export:

            mock_trigger_instance = mock_trigger_cls.return_value
            mock_trigger_instance.notify_audit_system.return_value = notification_res
            mock_validate.side_effect = Exception(uuid.uuid4().hex)
            mock_export.side_effect = Exception(uuid.uuid4().hex)

            hub = StressAuditSchedulerHub()
            res = hub.dispatch_alert_and_check(audit_id, message, storage_target, export_format)

            expected_dict = {
                "notification": notification_res,
                "is_valid": False,
                "export_data": {}
            }
            self.assertEqual(res, expected_dict)

    def test_market_portfolio_stress_audit_scheduler_hub_process(self):
        portfolio_id = uuid.uuid4().hex
        threshold = random.uniform(1.0, 100.0)
        storage_target = uuid.uuid4().hex
        audit_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        trigger_mock_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(StressAuditSchedulerHub, "run_audit_cycle", return_value=trigger_mock_result) as mock_run_cycle, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:
            
            res = market_portfolio_stress_audit_scheduler_hub_process(portfolio_id, threshold, storage_target, audit_data)

            expected_res = {
                "trigger_result": trigger_mock_result,
                "vault_storage": storage_target
            }
            self.assertEqual(res, expected_res)
            mock_run_cycle.assert_called_once_with(portfolio_id, threshold, storage_target)
            mock_vault_process.assert_called_once_with(storage_target, audit_data)