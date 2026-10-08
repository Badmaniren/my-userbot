import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)


class TestMarketPortfolioStressAuditSchedulerHub(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.threshold = random.uniform(0.01, 0.99)
        self.storage_target = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.feed_url = f"https://{ ''.join(random.choices(string.ascii_lowercase, k=8)) }.com/{str(uuid.uuid4())}"
        self.audit_id = str(uuid.uuid4())
        self.message = ''.join(random.choices(string.ascii_letters, k=15))
        self.export_format = random.choice(["json", "csv", "xml"])
        self.audit_data = {"metric": random.randint(100, 999), "status": "active"}

    @patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger")
    @patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process")
    def test_run_audit_cycle_with_result(self, mock_vault_process, mock_trigger_cls):
        mock_trigger_instance = mock_trigger_cls.return_value
        expected_res = {"evaluated": True, "score": random.uniform(1.0, 10.0)}
        mock_trigger_instance.evaluate_and_trigger.return_value = expected_res

        hub = StressAuditSchedulerHub()
        result = hub.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

        self.assertEqual(result, expected_res)
        mock_trigger_instance.evaluate_and_trigger.assert_called_once_with(self.portfolio_id, self.threshold)
        mock_vault_process.assert_called_once_with(self.storage_target, expected_res)

    @patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger")
    @patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process")
    def test_run_audit_cycle_none_result(self, mock_vault_process, mock_trigger_cls):
        mock_trigger_instance = mock_trigger_cls.return_value
        mock_trigger_instance.evaluate_and_trigger.return_value = None

        hub = StressAuditSchedulerHub()
        result = hub.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

        self.assertIsNone(result)
        mock_trigger_instance.evaluate_and_trigger.assert_called_once_with(self.portfolio_id, self.threshold)
        mock_vault_process.assert_not_called()

    @patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger")
    def test_get_feed(self, mock_trigger_cls):
        mock_trigger_instance = mock_trigger_cls.return_value
        expected_feed = {"feed_id": str(uuid.uuid4()), "data": random.randint(1, 100)}
        mock_trigger_instance.fetch_external_stress_feed.return_value = expected_feed

        hub = StressAuditSchedulerHub()
        result = hub.get_feed(self.feed_url)

        self.assertEqual(result, expected_feed)
        mock_trigger_instance.fetch_external_stress_feed.assert_called_once_with(self.feed_url)

    @patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger")
    @patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate")
    @patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export")
    def test_dispatch_alert_and_check_success(self, mock_vault_export, mock_vault_validate, mock_trigger_cls):
        mock_trigger_instance = mock_trigger_cls.return_value
        notification_res = {"sent": True, "id": str(uuid.uuid4())}
        mock_trigger_instance.notify_audit_system.return_value = notification_res
        mock_vault_validate.return_value = True
        exported_payload = {"export_id": str(uuid.uuid4())}
        mock_vault_export.return_value = exported_payload

        hub = StressAuditSchedulerHub()
        result = hub.dispatch_alert_and_check(self.audit_id, self.message, self.storage_target, self.export_format)

        self.assertEqual(result["notification"], notification_res)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["export_data"], exported_payload)
        mock_trigger_instance.notify_audit_system.assert_called_once_with(self.audit_id, self.message)
        mock_vault_validate.assert_called_once_with(self.storage_target, self.audit_id)
        mock_vault_export.assert_called_once_with(self.storage_target, self.export_format)

    @patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger")
    @patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate")
    @patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export")
    def test_dispatch_alert_and_check_exceptions(self, mock_vault_export, mock_vault_validate, mock_trigger_cls):
        mock_trigger_instance = mock_trigger_cls.return_value
        notification_res = {"sent": False}
        mock_trigger_instance.notify_audit_system.return_value = notification_res
        mock_vault_validate.side_effect = Exception("Validation failure")
        mock_vault_export.side_effect = Exception("Export failure")

        hub = StressAuditSchedulerHub()
        result = hub.dispatch_alert_and_check(self.audit_id, self.message, self.storage_target, self.export_format)

        self.assertEqual(result["notification"], notification_res)
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["export_data"], {})

    @patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAuditSchedulerHub")
    @patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process")
    def test_market_portfolio_stress_audit_scheduler_hub_process(self, mock_vault_process, mock_scheduler_cls):
        mock_scheduler_instance = mock_scheduler_cls.return_value
        trigger_res = {"status": "triggered", "val": random.random()}
        mock_scheduler_instance.run_audit_cycle.return_value = trigger_res

        result = market_portfolio_stress_audit_scheduler_hub_process(
            self.portfolio_id, self.threshold, self.storage_target, self.audit_data
        )

        self.assertEqual(result["trigger_result"], trigger_res)
        self.assertEqual(result["vault_storage"], self.storage_target)
        mock_scheduler_instance.run_audit_cycle.assert_called_once_with(
            self.portfolio_id, self.threshold, self.storage_target
        )
        mock_vault_process.assert_called_once_with(self.storage_target, self.audit_data)


if __name__ == '__main__':
    unittest.main()