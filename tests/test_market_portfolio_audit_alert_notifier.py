import unittest
from unittest.mock import patch
import uuid
import random
import io

from skills.market_portfolio_audit_alert_notifier import (
    audit_compliance_and_notify,
    MarketPortfolioAuditAlertNotifierService
)

class TestMarketPortfolioAuditAlertNotifier(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"audit_{uuid.uuid4().hex}.db"
        self.export_path = f"export_{uuid.uuid4().hex}.json"
        self.telegram_token = f"{random.randint(100000, 999999)}:ABC-{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(1000000, 9999999))
        self.symbol = f"SYM{random.choice(['BTC', 'ETH', 'SOL'])}_{uuid.uuid4().hex[:4]}"
        self.url = f"https://api.{uuid.uuid4().hex[:6]}.market/v1/audit"
        self.severity_level = random.choice(["INFO", "WARNING", "CRITICAL", "FATAL"])
        self.min_threshold = round(random.uniform(1.0, 100.0), 2)
        self.channels = [random.choice(["telegram", "webhook", "email"])]
        self.message = f"Audit integrity breach detected: {uuid.uuid4().hex}"

    @patch('skills.market_portfolio_audit_alert_notifier.MarketPortfolioAuditComplianceHub')
    @patch('skills.market_portfolio_audit_alert_notifier.dispatch_portfolio_alerts')
    def test_audit_compliance_and_notify_success(self, mock_dispatch, mock_hub_class):
        mock_hub_instance = mock_hub_class.return_value
        mock_hub_instance.check_compliance_integrity.return_value = True

        result = audit_compliance_and_notify(
            storage_file=self.storage_file,
            export_path=self.export_path,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            symbol=self.symbol,
            url=self.url,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertTrue(result)
        mock_hub_instance.check_compliance_integrity.assert_called_once()
        mock_dispatch.assert_called_once_with(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

    @patch('skills.market_portfolio_audit_alert_notifier.MarketPortfolioAuditComplianceHub')
    @patch('skills.market_portfolio_audit_alert_notifier.dispatch_portfolio_alerts')
    def test_audit_compliance_and_notify_failure(self, mock_dispatch, mock_hub_class):
        mock_hub_instance = mock_hub_class.return_value
        mock_hub_instance.check_compliance_integrity.return_value = False

        result = audit_compliance_and_notify(
            storage_file=self.storage_file,
            export_path=self.export_path,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            symbol=self.symbol,
            url=self.url,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertFalse(result)
        mock_hub_instance.check_compliance_integrity.assert_called_once()
        mock_dispatch.assert_not_called()

    @patch('skills.market_portfolio_audit_alert_notifier.MarketPortfolioAuditComplianceHub')
    @patch('skills.market_portfolio_audit_alert_notifier.send_telegram_notification')
    def test_service_trigger_alert_on_violation(self, mock_send_telegram, mock_hub_class):
        mock_hub_instance = mock_hub_class.return_value

        service = MarketPortfolioAuditAlertNotifierService(
            db_storage=self.storage_file,
            token=self.telegram_token,
            chat_id=self.chat_id
        )

        service.trigger_alert_on_violation(message=self.message)

        mock_hub_instance.verify_log_integrity.assert_called_once()
        mock_send_telegram.assert_called_once_with(
            token=self.telegram_token,
            chat_id=self.chat_id,
            message=self.message
        )

    @patch('skills.market_portfolio_audit_alert_notifier.MarketPortfolioAuditComplianceHub')
    def test_service_process_and_audit_stream_with_summary(self, mock_hub_class):
        mock_hub_instance = mock_hub_class.return_value
        expected_summary = {"status": "audited", "metric": random.randint(10, 500)}
        mock_hub_instance.get_audit_stream_summary.return_value = expected_summary
        
        stream_data = io.BytesIO(uuid.uuid4().bytes)

        service = MarketPortfolioAuditAlertNotifierService(
            db_storage=self.storage_file,
            token=self.telegram_token,
            chat_id=self.chat_id
        )

        result = service.process_and_audit_stream(
            export_path=self.export_path,
            stream=stream_data
        )

        self.assertEqual(result, expected_summary)
        mock_hub_instance.process_audit_stream_data.assert_called_once_with(
            export_path=self.export_path,
            stream=stream_data
        )
        mock_hub_instance.get_audit_stream_summary.assert_called_once()

    @patch('skills.market_portfolio_audit_alert_notifier.MarketPortfolioAuditComplianceHub')
    def test_service_process_and_audit_stream_fallback(self, mock_hub_class):
        mock_hub_instance = mock_hub_class.return_value
        mock_hub_instance.get_audit_stream_summary.return_value = None
        expected_res = {"processed": random.choice([True, False])}
        mock_hub_instance.process_audit_stream_data.return_value = expected_res
        
        stream_data = io.BytesIO(uuid.uuid4().bytes)

        service = MarketPortfolioAuditAlertNotifierService(
            db_storage=self.storage_file,
            token=self.telegram_token,
            chat_id=self.chat_id
        )

        result = service.process_and_audit_stream(
            export_path=self.export_path,
            stream=stream_data
        )

        self.assertEqual(result, expected_res)
        mock_hub_instance.process_audit_stream_data.assert_called_once_with(
            export_path=self.export_path,
            stream=stream_data
        )
        mock_hub_instance.get_audit_stream_summary.assert_called_once()

if __name__ == '__main__':
    unittest.main()