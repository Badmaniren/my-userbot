import unittest
from unittest.mock import patch
import random
import uuid
import string

from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)


class TestStressAuditSchedulerHub(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.threshold = round(random.uniform(0.01, 0.99), 4)
        self.storage_target = f"/storage/vault_{uuid.uuid4().hex[:6]}"
        self.feed_url = f"https://api.risk-feed-{uuid.uuid4().hex[:6]}.io/stress"
        self.audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        self.message = "".join(random.choices(string.ascii_letters + string.whitespace, k=24))
        self.export_format = random.choice(["json", "csv", "xml", "parquet"])
        self.audit_data = {
            "metric": random.choice(["VaR", "ExpectedShortfall", "MaxDrawdown"]),
            "value": round(random.uniform(100.0, 50000.0), 2),
            "token": uuid.uuid4().hex
        }

    def test_run_audit_cycle_success(self):
        mock_eval_result = {
            "status": "TRIGGERED",
            "score": round(random.uniform(1.0, 10.0), 2),
            "uid": uuid.uuid4().hex
        }

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            instance = MockTriggerClass.return_value
            instance.evaluate_and_trigger.return_value = mock_eval_result

            hub = StressAuditSchedulerHub()
            res = hub.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

            instance.evaluate_and_trigger.assert_called_once_with(self.portfolio_id, self.threshold)
            mock_vault_process.assert_called_once_with(self.storage_target, mock_eval_result)
            self.assertEqual(res, mock_eval_result)

    def test_run_audit_cycle_none_result(self):
        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            instance = MockTriggerClass.return_value
            instance.evaluate_and_trigger.return_value = None

            hub = StressAuditSchedulerHub()
            res = hub.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

            instance.evaluate_and_trigger.assert_called_once_with(self.portfolio_id, self.threshold)
            mock_vault_process.assert_not_called()
            self.assertIsNone(res)

    def test_get_feed_success(self):
        expected_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass:
            instance = MockTriggerClass.return_value
            instance.fetch_external_stress_feed.return_value = expected_bytes

            hub = StressAuditSchedulerHub()
            res = hub.get_feed(self.feed_url)

            instance.fetch_external_stress_feed.assert_called_once_with(self.feed_url)
            self.assertEqual(res, expected_bytes)

    def test_get_feed_exception(self):
        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass:
            instance = MockTriggerClass.return_value
            instance.fetch_external_stress_feed.side_effect = RuntimeError(f"Network error {uuid.uuid4().hex[:4]}")

            hub = StressAuditSchedulerHub()
            res = hub.get_feed(self.feed_url)

            instance.fetch_external_stress_feed.assert_called_once_with(self.feed_url)
            self.assertEqual(res, b"")

    def test_dispatch_alert_and_check_strict_success(self):
        notification_result = {"delivered": True, "code": random.randint(200, 299)}
        export_payload = {"data_hash": uuid.uuid4().hex, "items": random.randint(1, 100)}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate") as mock_validate, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export") as mock_export:

            instance = MockTriggerClass.return_value
            instance.notify_audit_system.return_value = notification_result
            mock_validate.return_value = True
            mock_export.return_value = export_payload

            hub = StressAuditSchedulerHub()
            result = hub.dispatch_alert_and_check(self.audit_id, self.message, self.storage_target, self.export_format)

            instance.notify_audit_system.assert_called_once_with(self.audit_id, self.message)
            mock_validate.assert_called_once_with(self.storage_target, self.audit_id)
            mock_export.assert_called_once_with(self.storage_target, self.export_format)

            self.assertEqual(result["notification"], notification_result)
            self.assertTrue(result["is_valid"])
            self.assertEqual(result["export_data"], export_payload)

    def test_dispatch_alert_and_check_strict_exceptions(self):
        notification_result = {"delivered": False, "reason": "timeout"}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate") as mock_validate, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export") as mock_export:

            instance = MockTriggerClass.return_value
            instance.notify_audit_system.return_value = notification_result
            mock_validate.side_effect = ValueError(f"Invalid storage {uuid.uuid4().hex}")
            mock_export.side_effect = KeyError(f"Missing format {uuid.uuid4().hex}")

            hub = StressAuditSchedulerHub()
            result = hub.dispatch_alert_and_check(self.audit_id, self.message, self.storage_target, self.export_format)

            instance.notify_audit_system.assert_called_once_with(self.audit_id, self.message)
            mock_validate.assert_called_once_with(self.storage_target, self.audit_id)
            mock_export.assert_called_once_with(self.storage_target, self.export_format)

            self.assertEqual(result["notification"], notification_result)
            self.assertFalse(result["is_valid"])
            self.assertEqual(result["export_data"], {})

    def test_scheduler_hub_process(self):
        sub_trigger_result = {"id": uuid.uuid4().hex, "action": "REBALANCE"}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAuditSchedulerHub.run_audit_cycle") as mock_run_cycle, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            mock_run_cycle.return_value = sub_trigger_result

            res = market_portfolio_stress_audit_scheduler_hub_process(
                self.portfolio_id,
                self.threshold,
                self.storage_target,
                self.audit_data
            )

            mock_run_cycle.assert_called_once_with(self.portfolio_id, self.threshold, self.storage_target)
            mock_vault_process.assert_called_once_with(self.storage_target, self.audit_data)

            self.assertEqual(res["trigger_result"], sub_trigger_result)
            self.assertEqual(res["vault_storage"], self.storage_target)


if __name__ == "__main__":
    unittest.main()