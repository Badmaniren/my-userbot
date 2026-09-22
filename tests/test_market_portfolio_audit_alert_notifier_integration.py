import unittest
import os
import uuid
from skills.market_portfolio_audit_alert_notifier import (
    audit_compliance_and_notify,
    MarketPortfolioAuditAlertNotifierService
)

class TestMarketPortfolioAuditAlertNotifierIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_audit_storage_{self.random_suffix}.json"
        self.export_path = f"test_export_path_{self.random_suffix}.json"
        self.telegram_token = f"test_token_{self.random_suffix}"
        self.chat_id = f"test_chat_{self.random_suffix}"
        self.symbol = f"BTC_{self.random_suffix}"
        self.url = f"https://api.example.com/price/{self.random_suffix}"
        self.severity_level = "HIGH"
        self.min_threshold = 100.5
        self.channels = ["telegram"]

    def tearDown(self):
        for f in [self.storage_file, self.export_path]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

    def test_audit_compliance_and_notify_integration(self):
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
        self.assertIsInstance(result, bool)

    def test_service_workflow_integration(self):
        service = MarketPortfolioAuditAlertNotifierService(
            db_storage=self.storage_file,
            token=self.telegram_token,
            chat_id=self.chat_id
        )
        
        test_message = f"Violation alert message {self.random_suffix}"
        
        try:
            service.trigger_alert_on_violation(message=test_message)
        except Exception:
            pass

        stream_data = [
            {"id": self.random_suffix, "status": "violation", "value": 99.9}
        ]
        
        stream_result = service.process_and_audit_stream(
            export_path=self.export_path,
            stream=stream_data
        )
        
        self.assertIsNotNone(stream_result)

if __name__ == "__main__":
    unittest.main()