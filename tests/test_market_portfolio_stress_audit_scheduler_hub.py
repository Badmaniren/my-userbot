import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)


class TestStressAuditSchedulerHub(unittest.TestCase):

    def test_scheduler_hub_run_audit_cycle_success(self):
        portfolio_id = uuid.uuid4().hex
        threshold = random.uniform(1.0, 100.0)
        storage_target = uuid.uuid4().hex
        mock_result = {"audit_id": uuid.uuid4().hex, "status": "triggered"}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as mock_trigger_cls, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:
            
            instance = mock_trigger_cls.return_value
            instance.evaluate_and_trigger.return_value = mock_result

            hub = StressAuditSchedulerHub()
            res = hub.run_audit_cycle(portfolio_id, threshold, storage_target)

            self.assertEqual(res, mock_result)
            instance.evaluate_and_trigger.assert_called_once_with(portfolio_id, threshold)
            mock_vault_process.assert_called_once_with(storage_target, mock_result)

    def test_scheduler_hub_run_audit_cycle_none(self):
        portfolio_id = uuid.uuid4().hex
        threshold = random.uniform(1.0, 100.0)
        storage_target = uuid.uuid4().hex

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as mock_trigger_cls, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:
            
            instance = mock_trigger_cls.return_value
            instance.evaluate_and_trigger.return_value = None

            hub = StressAuditSchedulerHub()
            res = hub.run_audit_cycle(portfolio_id, threshold, storage_target)

            self.assertIsNone(res)
            instance.evaluate_and_trigger.assert_called_once_with(portfolio_id, threshold)
            mock_vault_process.assert_not_called()

    def test_scheduler_hub_fetch_feed(self):
        feed_url = f"https://{uuid.uuid4().hex}.internal/stress-feed"
        random_bytes = uuid.uuid4().hex.encode('utf-8')

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as mock_trigger_cls:
            instance = mock_trigger_cls.return_value
            instance.fetch_external_stress_feed.return_value = random_bytes

            hub = StressAuditSchedulerHub()
            res = hub.get_feed(feed_url)

            self.assertEqual(res, random_bytes)
            instance.fetch_external_stress_feed.assert_called_once_with(feed_url)

    def test_scheduler_hub_dispatch_alert_and_check(self):
        audit_id = uuid.uuid4().hex
        message = "".join(random.choices(string.ascii_letters, k=10))
        storage_target = uuid.uuid4().hex
        export_format = uuid.uuid4().hex

        notification_result = {"status": "notified", "id": audit_id}
        is_valid_result = random.choice([True, False])
        export_data_result = {"data": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as mock_trigger_cls, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate") as mock_vault_validate, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export") as mock_vault_export:
            
            instance = mock_trigger_cls.return_value
            instance.notify_audit_system.return_value = notification_result
            mock_vault_validate.return_value = is_valid_result
            mock_vault_export.return_value = export_data_result

            hub = StressAuditSchedulerHub()
            result = hub.dispatch_alert_and_check(audit_id, message, storage_target, export_format)

            self.assertEqual(result["notification"], notification_result)
            self.assertEqual(result["is_valid"], is_valid_result)
            self.assertEqual(result["export_data"], export_data_result)

            instance.notify_audit_system.assert_called_once_with(audit_id, message)
            mock_vault_validate.assert_called_once_with(storage_target, audit_id)
            mock_vault_export.assert_called_once_with(storage_target, export_format)

    def test_market_portfolio_stress_audit_scheduler_hub_process(self):
        portfolio_id = uuid.uuid4().hex
        threshold = random.uniform(1.0, 100.0)
        storage_target = uuid.uuid4().hex
        audit_data = {"audit_detail": uuid.uuid4().hex}
        trigger_output = {"triggered": True}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAuditSchedulerHub.run_audit_cycle") as mock_run_cycle, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:
            
            mock_run_cycle.return_value = trigger_output

            result = market_portfolio_stress_audit_scheduler_hub_process(portfolio_id, threshold, storage_target, audit_data)

            expected_result = {
                "trigger_result": trigger_output,
                "vault_storage": storage_target
            }

            self.assertEqual(result, expected_result)
            mock_run_cycle.assert_called_once_with(portfolio_id, threshold, storage_target)
            mock_vault_process.assert_called_once_with(storage_target, audit_data)


if __name__ == "__main__":
    unittest.main()