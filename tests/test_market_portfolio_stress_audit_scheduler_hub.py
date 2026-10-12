import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)


class TestStressAuditSchedulerHub(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.threshold = random.uniform(1.0, 100.0)
        self.storage_target = f"/tmp/{uuid.uuid4().hex}.vault"
        self.audit_id = str(uuid.uuid4())
        self.feed_url = f"https://{uuid.uuid4().hex}.com/feed"
        self.export_format = random.choice(["json", "csv", "xml", "yaml"])
        self.message = "".join(random.choices(string.ascii_letters + " ", k=25))
        self.audit_data = {
            "audit_code": uuid.uuid4().hex,
            "metrics": random.randint(100, 9999)
        }

    def test_run_audit_cycle_success(self):
        eval_result = {"status": "triggered", "value": random.randint(1, 50)}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger.evaluate_and_trigger", return_value=eval_result) as mock_trigger, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            scheduler = StressAuditSchedulerHub()
            res = scheduler.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

            mock_trigger.assert_called_once_with(self.portfolio_id, self.threshold)
            mock_vault_process.assert_called_once_with(self.storage_target, eval_result)
            self.assertEqual(res, eval_result)

    def test_run_audit_cycle_none_result(self):
        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger.evaluate_and_trigger", return_value=None) as mock_trigger, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            scheduler = StressAuditSchedulerHub()
            res = scheduler.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

            mock_trigger.assert_called_once_with(self.portfolio_id, self.threshold)
            mock_vault_process.assert_not_called()
            self.assertIsNone(res)

    def test_get_feed_success(self):
        expected_feed = {"feed_id": uuid.uuid4().hex, "data": random.random()}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger.fetch_external_stress_feed", return_value=expected_feed) as mock_fetch:
            scheduler = StressAuditSchedulerHub()
            feed = scheduler.get_feed(self.feed_url)

            mock_fetch.assert_called_once_with(self.feed_url)
            self.assertEqual(feed, expected_feed)

    def test_dispatch_alert_and_check_all_success(self):
        notification_result = {"delivered": True, "token": uuid.uuid4().hex}
        is_valid_result = True
        export_result = io.BytesIO(uuid.uuid4().bytes)

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger.notify_audit_system", return_value=notification_result) as mock_notify, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate", return_value=is_valid_result) as mock_validate, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export", return_value=export_result) as mock_export:

            scheduler = StressAuditSchedulerHub()
            result = scheduler.dispatch_alert_and_check(
                self.audit_id, self.message, self.storage_target, self.export_format
            )

            mock_notify.assert_called_once_with(self.audit_id, self.message)
            mock_validate.assert_called_once_with(self.storage_target, self.audit_id)
            mock_export.assert_called_once_with(self.storage_target, self.export_format)

            self.assertEqual(result["notification"], notification_result)
            self.assertEqual(result["is_valid"], is_valid_result)
            self.assertEqual(result["export_data"], export_result)

    def test_market_portfolio_stress_audit_scheduler_hub_process(self):
        trigger_output = {"action": uuid.uuid4().hex, "metric": random.uniform(0.1, 99.9)}

        with patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAuditSchedulerHub.run_audit_cycle", return_value=trigger_output) as mock_run_cycle, \
             patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process") as mock_vault_process:

            process_res = market_portfolio_stress_audit_scheduler_hub_process(
                self.portfolio_id, self.threshold, self.storage_target, self.audit_data
            )

            mock_run_cycle.assert_called_once_with(self.portfolio_id, self.threshold, self.storage_target)
            mock_vault_process.assert_called_once_with(self.storage_target, self.audit_data)

            self.assertEqual(process_res["trigger_result"], trigger_output)
            self.assertEqual(process_res["vault_storage"], self.storage_target)


if __name__ == "__main__":
    unittest.main()