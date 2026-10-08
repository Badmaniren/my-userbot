import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub
)


class TestStressAuditSchedulerHub(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.threshold = random.uniform(0.01, 0.99)
        self.storage_target = f"storage_{uuid.uuid4().hex}"
        self.audit_id = str(uuid.uuid4())
        self.message = f"msg_{uuid.uuid4().hex}"
        self.feed_url = f"https://stress-feed-{uuid.uuid4().hex}.internal/api"
        self.export_format = random.choice(["json", "csv", "pdf"])

    def test_scheduler_hub_initialization_and_orchestration(self):
        scheduler = StressAuditSchedulerHub()
        self.assertIsNotNone(scheduler)

        mock_trigger_result = {
            "triggered": True,
            "action": f"rebalance_{uuid.uuid4().hex}",
            "score": random.uniform(1.0, 100.0)
        }

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            instance = MockTriggerClass.return_value
            instance.evaluate_and_trigger.return_value = mock_trigger_result

            res = scheduler.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

            self.assertEqual(res, mock_trigger_result)
            instance.evaluate_and_trigger.assert_called_once_with(self.portfolio_id, self.threshold)
            mock_vault_process.assert_called_once()

    def test_scheduler_hub_no_trigger_action(self):
        scheduler = StressAuditSchedulerHub()

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            instance = MockTriggerClass.return_value
            instance.evaluate_and_trigger.return_value = None

            res = scheduler.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

            self.assertIsNone(res)
            instance.evaluate_and_trigger.assert_called_once_with(self.portfolio_id, self.threshold)
            mock_vault_process.assert_not_called()

    def test_scheduler_hub_fetch_feed(self):
        scheduler = StressAuditSchedulerHub()
        random_bytes = "".join(random.choices(string.ascii_letters, k=32)).encode('utf-8')

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass:
            instance = MockTriggerClass.return_value
            instance.fetch_external_stress_feed.return_value = io.BytesIO(random_bytes)

            feed_res = scheduler.get_feed(self.feed_url)
            self.assertEqual(feed_res.read(), random_bytes)
            instance.fetch_external_stress_feed.assert_called_once_with(self.feed_url)

    def test_scheduler_hub_notify_and_validate(self):
        scheduler = StressAuditSchedulerHub()
        mock_notify_res = {"status": "ok", "alert_code": uuid.uuid4().int}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger") as MockTriggerClass, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate") as mock_validate, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export") as mock_export:

            instance = MockTriggerClass.return_value
            instance.notify_audit_system.return_value = mock_notify_res
            mock_validate.return_value = True
            mock_export.return_value = f"exported_{uuid.uuid4().hex}"

            notif_res = scheduler.dispatch_alert_and_check(self.audit_id, self.message, self.storage_target, self.export_format)

            self.assertEqual(notif_res["notification"], mock_notify_res)
            self.assertTrue(notif_res["is_valid"])
            self.assertIn("exported", notif_res["export_data"])

            instance.notify_audit_system.assert_called_once_with(self.audit_id, self.message)
            mock_validate.assert_called_once_with(self.storage_target, self.audit_id)
            mock_export.assert_called_once_with(self.storage_target, self.export_format)


if __name__ == '__main__':
    unittest.main()