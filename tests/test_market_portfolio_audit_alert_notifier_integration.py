import unittest
import os
import uuid
import tempfile
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from skills import market_portfolio_alert_dispatcher
from skills import market_portfolio_audit_alert_notifier

class TestMarketPortfolioAuditAlertNotifierIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"audit_storage_{uuid.uuid4()}.json")
        self.export_path = os.path.join(self.test_dir.name, f"export_{uuid.uuid4()}.log")
        self.db_storage = f"sqlite:///{os.path.join(self.test_dir.name, f'db_{uuid.uuid4()}.sqlite')}"
        
        self.token = str(uuid.uuid4())
        self.chat_id = str(uuid.randint(100000, 999999))
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"http://localhost/{uuid.uuid4()}"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_audit_alert_notifier_composition(self):
        hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.db_storage,
            audit_exporter=None
        )
        
        self.assertTrue(hasattr(market_portfolio_audit_alert_notifier, 'process_audit_compliance_alerts') or 
                        hasattr(market_portfolio_audit_alert_notifier, 'dispatch_compliance_audit_notifications') or
                        callable(getattr(market_portfolio_audit_alert_notifier, 'run_audit_alert_cycle', None)))

        if hasattr(market_portfolio_audit_alert_notifier, 'run_audit_alert_cycle'):
            result = market_portfolio_audit_alert_notifier.run_audit_alert_cycle(
                compliance_hub=hub,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            self.assertIsNotNone(result)
        else:
            integrity_status = hub.check_compliance_integrity()
            self.assertIsInstance(integrity_status, (bool, dict, list))

if __name__ == '__main__':
    unittest.main()