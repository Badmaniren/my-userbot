import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills import market_portfolio_stress_alert_trigger


class TestMarketPortfolioStressAlertTrigger(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"/tmp/{uuid.uuid4().hex}.db"
        self.expected_audit_id = uuid.uuid4().hex
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/webhook"
        self.telegram_token = f"{random.randint(1000, 9999)}:{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(100000, 9999999))
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.min_threshold = round(random.uniform(5.0, 25.0), 2)
        self.channels = [random.choice(["telegram", "webhook", "email"])]

    @patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_validate")
    @patch("skills.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts")
    def test_check_stress_thresholds_and_alert_breach_status(self, mock_dispatch, mock_validate):
        audit_data = {
            "status": "BREACH",
            "max_drawdown": random.uniform(0.0, 4.0)
        }
        mock_validate.return_value = audit_data

        result = market_portfolio_stress_alert_trigger.check_stress_thresholds_and_alert(
            storage_target=self.storage_file,
            expected_audit_id=self.expected_audit_id,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertTrue(result)
        mock_validate.assert_called_once_with(self.storage_file, self.expected_audit_id)
        mock_dispatch.assert_called_once_with(
            self.symbol,
            self.url,
            self.telegram_token,
            self.chat_id,
            self.storage_file,
            self.severity_level,
            self.min_threshold,
            self.channels
        )

    @patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_validate")
    @patch("skills.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts")
    def test_check_stress_thresholds_and_alert_exceeds_threshold(self, mock_dispatch, mock_validate):
        audit_data = {
            "status": "NORMAL",
            "max_drawdown": self.min_threshold + random.uniform(1.0, 10.0)
        }
        mock_validate.return_value = audit_data

        result = market_portfolio_stress_alert_trigger.check_stress_thresholds_and_alert(
            storage_target=self.storage_file,
            expected_audit_id=self.expected_audit_id,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertTrue(result)
        mock_dispatch.assert_called_once()

    @patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_validate")
    @patch("skills.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts")
    def test_check_stress_thresholds_and_alert_no_breach(self, mock_dispatch, mock_validate):
        audit_data = {
            "status": "NORMAL",
            "max_drawdown": self.min_threshold - random.uniform(0.1, 5.0)
        }
        mock_validate.return_value = audit_data

        result = market_portfolio_stress_alert_trigger.check_stress_thresholds_and_alert(
            storage_target=self.storage_file,
            expected_audit_id=self.expected_audit_id,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertFalse(result)
        mock_dispatch.assert_not_called()

    @patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_validate")
    @patch("skills.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts")
    def test_check_stress_thresholds_and_alert_empty_data(self, mock_dispatch, mock_validate):
        mock_validate.return_value = None

        result = market_portfolio_stress_alert_trigger.check_stress_thresholds_and_alert(
            storage_target=self.storage_file,
            expected_audit_id=self.expected_audit_id,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertIsNone(result)
        mock_dispatch.assert_not_called()

    @patch("skills.market_portfolio_stress_audit_summary_vault.start_new")
    @patch("skills.market_portfolio_stress_alert_trigger.check_stress_thresholds_and_alert")
    def test_run_success_with_storage_arg(self, mock_check, mock_start_new):
        mock_check.return_value = True

        result = market_portfolio_stress_alert_trigger.run(
            storage_file=self.storage_file,
            expected_audit_id=self.expected_audit_id,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertTrue(result)
        mock_start_new.assert_called_once_with(self.storage_file)
        mock_check.assert_called_once_with(
            storage_target=self.storage_file,
            expected_audit_id=self.expected_audit_id,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

    @patch("skills.market_portfolio_stress_audit_summary_vault.start_new")
    @patch("skills.market_portfolio_stress_alert_trigger.check_stress_thresholds_and_alert")
    def test_run_fallback_start_new_without_args(self, mock_check, mock_start_new):
        mock_start_new.side_effect = [TypeError("Unexpected argument"), None]
        mock_check.return_value = False

        result = market_portfolio_stress_alert_trigger.run(
            storage_file=self.storage_file,
            expected_audit_id=self.expected_audit_id,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertFalse(result)
        self.assertEqual(mock_start_new.call_count, 2)
        mock_start_new.assert_any_call(self.storage_file)
        mock_start_new.assert_any_call()
        mock_check.assert_called_once()