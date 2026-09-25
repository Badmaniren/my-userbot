import unittest
import os
import uuid
import random
from skills.db_storage import MarketParser
from skills.market_portfolio_monitor import start_new, export_audit_logs, run_compliance_export

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_storage_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"db_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)} "
        self.url = f"https://api.market.internal/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.db = MarketParser(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_full_monitoring_pipeline_integration(self):
        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.storage_file))
        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported)
        compliance_exported = run_compliance_export(storage_file=self.storage_file)
        self.assertTrue(compliance_exported)

if __name__ == "__main__":
    unittest.main()
