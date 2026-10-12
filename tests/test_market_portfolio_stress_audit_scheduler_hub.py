import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.market_portfolio_stress_audit_scheduler_hub import (
    StressAuditSchedulerHub,
    market_portfolio_stress_audit_scheduler_hub_process
)


class TestMarketPortfolioStressAuditSchedulerHub(unittest.TestCase):

    def setUp(self) -> None:
        self.portfolio_id = uuid.uuid4().hex
        self.threshold = round(random.uniform(0.01, 0.99), 4)
        self.storage_target = uuid.uuid4().hex
        self.feed_url = f"https://{uuid.uuid4().hex}.com/feed"
        self.audit_id = uuid.uuid4().hex
        self.message = uuid.uuid4().hex
        self.export_format = random.choice(["json", "csv", "xml"])
        self.audit_data = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}

    @patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger")
    @patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process")
    def test_run_audit_cycle_success(self, mock_vault_process: MagicMock, mock_trigger_cls: MagicMock) -> None:
        mock_instance = mock_trigger_cls.return_value
        expected_res = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_instance.evaluate_and_trigger.return_value = expected_res

        hub = StressAuditSchedulerHub()
        result = hub.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

        self.assertEqual(result, expected_res)
        mock_instance.evaluate_and_trigger.assert_called_once_with(self.portfolio_id, self.threshold)
        mock_vault_process.assert_called_once_with(self.storage_target, expected_res)

    @patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger")
    @patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process")
    def test_run_audit_cycle_none_result(self, mock_vault_process: MagicMock, mock_trigger_cls: MagicMock) -> None:
        mock_instance = mock_trigger_cls.return_value
        mock_instance.evaluate_and_trigger.return_value = None

        hub = StressAuditSchedulerHub()
        result = hub.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

        self.assertIsNone(result)
        mock_instance.evaluate_and_trigger.assert_called_once_with(self.portfolio_id, self.threshold)
        mock_vault_process.assert_not_called()

    @patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger")
    def test_run_audit_cycle_exception_raises(self, mock_trigger_cls: MagicMock) -> None:
        mock_instance = mock_trigger_cls.return_value
        mock_instance.evaluate_and_trigger.side_effect = RuntimeError(uuid.uuid4().hex)

        hub = StressAuditSchedulerHub()
        with self.assertRaises(RuntimeError):
            hub.run_audit_cycle(self.portfolio_id, self.threshold, self.storage_target)

    @patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger")
    def test_get_feed_success(self, mock_trigger_cls: MagicMock) -> None:
        mock_instance = mock_trigger_cls.return_value
        expected_bytes = uuid.uuid4().hex.encode("utf-8")
        mock_instance.fetch_external_stress_feed.return_value = expected_bytes

        hub = StressAuditSchedulerHub()
        result = hub.get_feed(self.feed_url)

        self.assertEqual(result, expected_bytes)
        mock_instance.fetch_external_stress_feed.assert_called_once_with(self.feed_url)

    @patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger")
    def test_get_feed_exception_raises(self, mock_trigger_cls: MagicMock) -> None:
        mock_instance = mock_trigger_cls.return_value
        mock_instance.fetch_external_stress_feed.side_effect = ValueError(uuid.uuid4().hex)

        hub = StressAuditSchedulerHub()
        with self.assertRaises(ValueError):
            hub.get_feed(self.feed_url)

    @patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_export")
    @patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_validate")
    @patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAutoRebalanceTrigger")
    def test_dispatch_alert_and_check(self, mock_trigger_cls: MagicMock, mock_validate: MagicMock, mock_export: MagicMock) -> None:
        mock_instance = mock_trigger_cls.return_value
        notification_res = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_instance.notify_audit_system.return_value = notification_res

        is_valid_val = random.choice([True, False])
        mock_validate.return_value = is_valid_val

        export_res = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_export.return_value = export_res

        hub = StressAuditSchedulerHub()
        result = hub.dispatch_alert_and_check(self.audit_id, self.message, self.storage_target, self.export_format)

        expected_dict = {
            "notification": notification_res,
            "is_valid": is_valid_val,
            "export_data": export_res
        }
        self.assertEqual(result, expected_dict)
        mock_instance.notify_audit_system.assert_called_once_with(self.audit_id, self.message)
        mock_validate.assert_called_once_with(self.storage_target, self.audit_id)
        mock_export.assert_called_once_with(self.storage_target, self.export_format)

    @patch("skills.market_portfolio_stress_audit_scheduler_hub.market_portfolio_stress_audit_summary_vault_process")
    @patch("skills.market_portfolio_stress_audit_scheduler_hub.StressAuditSchedulerHub")
    def test_market_portfolio_stress_audit_scheduler_hub_process(self, mock_scheduler_cls: MagicMock, mock_vault_process: MagicMock) -> None:
        mock_scheduler_instance = mock_scheduler_cls.return_value
        trigger_result_expected = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_scheduler_instance.run_audit_cycle.return_value = trigger_result_expected

        result = market_portfolio_stress_audit_scheduler_hub_process(
            self.portfolio_id, self.threshold, self.storage_target, self.audit_data
        )

        expected_result = {
            "trigger_result": trigger_result_expected,
            "vault_storage": self.storage_target
        }
        self.assertEqual(result, expected_result)
        mock_scheduler_instance.run_audit_cycle.assert_called_once_with(self.portfolio_id, self.threshold, self.storage_target)
        mock_vault_process.assert_called_once_with(self.storage_target, self.audit_data)


if __name__ == "__main__":
    unittest.main()