import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.market_portfolio_audit_alert_notifier import (
    audit_compliance_and_notify,
    MarketPortfolioAuditAlertNotifierService
)

class TestMarketPortfolioAuditAlertNotifier(unittest.TestCase):

    def setUp(self):
        self.rand_storage = f"storage_{uuid.uuid4().hex}.db"
        self.rand_export_path = f"export_{uuid.uuid4().hex}.json"
        self.rand_token = f"token_{uuid.uuid4().hex}"
        self.rand_chat_id = str(random.randint(100000, 999999))
        self.rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.rand_url = f"https://{uuid.uuid4().hex}.example/api"
        self.rand_severity = random.choice(["INFO", "WARNING", "CRITICAL", "FATAL"])
        self.rand_threshold = random.uniform(0.01, 0.99)
        self.rand_channels = [uuid.uuid4().hex, uuid.uuid4().hex]

    @patch('skills.market_portfolio_audit_alert_notifier.MarketPortfolioAuditComplianceHub')
    @patch('skills.market_portfolio_audit_alert_notifier.dispatch_portfolio_alerts')
    def test_audit_compliance_and_notify_success(self, mock_dispatch, mock_hub_class):
        mock_hub_instance = MagicMock()
        mock_hub_instance.check_compliance_integrity.return_value = True
        mock_hub_class.return_value = mock_hub_instance

        result = audit_compliance_and_notify(
            storage_file=self.rand_storage,
            export_path=self.rand_export_path,
            telegram_token=self.rand_token,
            chat_id=self.rand_chat_id,
            symbol=self.rand_symbol,
            url=self.rand_url,
            severity_level=self.rand_severity,
            min_threshold=self.rand_threshold,
            channels=self.rand_channels
        )

        mock_hub_class.assert_called_once_with(storage_file=self.rand_storage)
        mock_hub_instance.check_compliance_integrity.assert_called_once()
        mock_dispatch.assert_called_once_with(
            symbol=self.rand_symbol,
            url=self.rand_url,
            telegram_token=self.rand_token,
            chat_id=self.rand_chat_id,
            storage_file=self.rand_storage,
            severity_level=self.rand_severity,
            min_threshold=self.rand_threshold,
            channels=self.rand_channels
        )
        self.assertTrue(result)

    @patch('skills.market_portfolio_audit_alert_notifier.MarketPortfolioAuditComplianceHub')
    @patch('skills.market_portfolio_audit_alert_notifier.dispatch_portfolio_alerts')
    def test_audit_compliance_and_notify_integrity_failure(self, mock_dispatch, mock_hub_class):
        mock_hub_instance = MagicMock()
        mock_hub_instance.check_compliance_integrity.return_value = False
        mock_hub_class.return_value = mock_hub_instance

        result = audit_compliance_and_notify(
            storage_file=self.rand_storage,
            export_path=self.rand_export_path,
            telegram_token=self.rand_token,
            chat_id=self.rand_chat_id,
            symbol=self.rand_symbol,
            url=self.rand_url,
            severity_level=self.rand_severity,
            min_threshold=self.rand_threshold,
            channels=self.rand_channels
        )

        mock_hub_class.assert_called_once_with(storage_file=self.rand_storage)
        mock_hub_instance.check_compliance_integrity.assert_called_once()
        mock_dispatch.assert_not_called()
        self.assertFalse(result)

    @patch('skills.market_portfolio_audit_alert_notifier.MarketPortfolioAuditComplianceHub')
    @patch('skills.market_portfolio_audit_alert_notifier.send_telegram_notification')
    def test_service_class_trigger_alert(self, mock_send_telegram, mock_hub_class):
        mock_hub_instance = MagicMock()
        mock_hub_instance.verify_log_integrity.return_value = {"status": "violation", "id": uuid.uuid4().hex}
        mock_hub_class.return_value = mock_hub_instance

        service = MarketPortfolioAuditAlertNotifierService(
            db_storage=self.rand_storage,
            token=self.rand_token,
            chat_id=self.rand_chat_id
        )

        rand_msg = f"Violation detected: {uuid.uuid4().hex}"
        service.trigger_alert_on_violation(rand_msg)

        mock_send_telegram.assert_called_once_with(
            token=self.rand_token,
            chat_id=self.rand_chat_id,
            message=rand_msg
        )

    @patch('skills.market_portfolio_audit_alert_notifier.MarketPortfolioAuditComplianceHub')
    def test_service_stream_processing_with_io(self, mock_hub_class):
        mock_hub_instance = MagicMock()
        rand_summary = {"processed_records": random.randint(10, 100), "uuid": uuid.uuid4().hex}
        mock_hub_instance.get_audit_stream_summary.return_value = rand_summary
        mock_hub_class.return_value = mock_hub_instance

        service = MarketPortfolioAuditAlertNotifierService(
            db_storage=self.rand_storage,
            token=self.rand_token,
            chat_id=self.rand_chat_id
        )

        random_bytes = uuid.uuid4().bytes + b"".join(random.choices([b'\x00', b'\xff', b'\x42'], k=32))
        stream_mock = io.BytesIO(random_bytes)

        result = service.process_and_audit_stream(self.rand_export_path, stream_mock)

        mock_hub_instance.process_audit_stream_data.assert_called_once_with(
            export_path=self.rand_export_path,
            stream=stream_mock
        )
        self.assertEqual(result, rand_summary)

if __name__ == '__main__':
    unittest.main()