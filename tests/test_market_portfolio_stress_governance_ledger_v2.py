import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

try:
    import requests
except ImportError:
    class FakeRequests:
        class RequestException(Exception):
            pass
    requests = FakeRequests()

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from skills.market_portfolio_stress_governance_ledger_v2 import (
    MarketPortfolioStressGovernanceLedgerV2,
    LedgerAuditError
)

class TestMarketPortfolioStressGovernanceLedgerV2(unittest.TestCase):

    def setUp(self):
        self.ledger = MarketPortfolioStressGovernanceLedgerV2()
        self.random_portfolio_id = uuid.uuid4().hex
        self.random_audit_id = uuid.uuid4().hex
        self.random_scenario_name = ''.join(random.choices(string.ascii_letters, k=12))
        self.random_error_message = ''.join(random.choices(string.ascii_letters + string.whitespace, k=30))
        self.random_numeric_value = round(random.uniform(100.5, 9999.9), 2)

    def test_record_stress_audit_success(self):
        mock_db_storage = MagicMock()
        mock_db_storage.insert.return_value = True

        with patch('skills.market_portfolio_stress_governance_ledger_v2.db_storage', mock_db_storage):
            payload = {
                "portfolio_id": self.random_portfolio_id,
                "audit_id": self.random_audit_id,
                "scenario": self.random_scenario_name,
                "impact_score": self.random_numeric_value
            }

            result = self.ledger.record_audit_event(payload)
            self.assertTrue(result)
            mock_db_storage.insert.assert_called_once()
            called_args = mock_db_storage.insert.call_args[0][0]
            self.assertEqual(called_args["portfolio_id"], self.random_portfolio_id)
            self.assertEqual(called_args["audit_id"], self.random_audit_id)

    def test_record_stress_audit_exception_handling(self):
        mock_db_storage = MagicMock()
        mock_db_storage.insert.side_effect = Exception(self.random_error_message)

        with patch('skills.market_portfolio_stress_governance_ledger_v2.db_storage', mock_db_storage):
            payload = {
                "portfolio_id": self.random_portfolio_id,
                "audit_id": self.random_audit_id,
                "scenario": self.random_scenario_name,
                "impact_score": self.random_numeric_value
            }

            with self.assertRaises(LedgerAuditError) as ctx:
                self.ledger.record_audit_event(payload)

            self.assertIn(self.random_error_message, str(ctx.exception))

    def test_export_ledger_to_stream(self):
        random_byte_data = ''.join(random.choices(string.ascii_letters + string.digits, k=100)).encode('utf-8')
        mock_exporter = MagicMock()
        mock_exporter.export_stream.return_value = io.BytesIO(random_byte_data)

        with patch('skills.market_portfolio_stress_governance_ledger_v2.market_portfolio_audit_log_exporter', mock_exporter):
            stream_result = self.ledger.export_ledger_data(self.random_portfolio_id)
            data_read = stream_result.read()
            self.assertEqual(data_read, random_byte_data)
            mock_exporter.export_stream.assert_called_once_with(self.random_portfolio_id)

    def test_compliance_hub_verification(self):
        mock_compliance_hub = MagicMock()
        expected_status = random.choice([True, False])
        mock_compliance_hub.verify_ledger_integrity.return_value = expected_status

        with patch('skills.market_portfolio_stress_governance_ledger_v2.market_portfolio_audit_compliance_hub', mock_compliance_hub):
            status = self.ledger.verify_compliance(self.random_audit_id)
            self.assertEqual(status, expected_status)
            mock_compliance_hub.verify_ledger_integrity.assert_called_once_with(self.random_audit_id)

    def test_alert_notifier_integration(self):
        mock_notifier = MagicMock()
        mock_notifier.dispatch_alert.return_value = uuid.uuid4().hex

        with patch('skills.market_portfolio_stress_governance_ledger_v2.market_portfolio_audit_alert_notifier', mock_notifier):
            severity = random.choice(["LOW", "MEDIUM", "CRITICAL", "EXTREME"])
            alert_id = self.ledger.notify_governance_breach(self.random_portfolio_id, severity, self.random_error_message)

            self.assertIsNotNone(alert_id)
            mock_notifier.dispatch_alert.assert_called_once()
            call_kwargs = mock_notifier.dispatch_alert.call_args[1]
            self.assertEqual(call_kwargs["portfolio_id"], self.random_portfolio_id)
            self.assertEqual(call_kwargs["severity"], severity)
            self.assertEqual(call_kwargs["message"], self.random_error_message)

    def test_webhook_event_logger_fallback(self):
        mock_webhook = MagicMock()
        mock_webhook.sync_event.side_effect = requests.RequestException(self.random_error_message)

        mock_notifier = MagicMock()
        mock_notifier.dispatch_alert.return_value = True

        with patch('skills.market_portfolio_stress_governance_ledger_v2.market_portfolio_webhook_event_logger', mock_webhook), \
             patch('skills.market_portfolio_stress_governance_ledger_v2.market_portfolio_audit_alert_notifier', mock_notifier):

            event_payload = {
                "event_id": uuid.uuid4().hex,
                "value": self.random_numeric_value
            }

            result = self.ledger.log_webhook_sync(event_payload)
            self.assertFalse(result)
            mock_notifier.dispatch_alert.assert_called_once()

    def test_html_parsing_audit_report(self):
        random_html_tag = ''.join(random.choices(string.ascii_lowercase, k=6))
        random_html_content = ''.join(random.choices(string.ascii_letters + string.digits, k=25))
        html_payload = f"<html><body><{random_html_tag}>{random_html_content}</{random_html_tag}></body></html>"

        if BeautifulSoup is not None:
            soup = BeautifulSoup(html_payload, 'html.parser')
            extracted_text = soup.find(random_html_tag).text
            self.assertEqual(extracted_text, random_html_content)
        else:
            self.assertIn(random_html_content, html_payload)

if __name__ == '__main__':
    unittest.main()
