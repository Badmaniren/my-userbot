import unittest
import os
import tempfile
import uuid
import random
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4()}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.test-monitor.org/v1/{uuid.uuid4()}"
        self.telegram_token = f"tok_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 99999999))

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pipeline_integration_flow(self):
        result_new = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_new)
        self.assertTrue(os.path.exists(self.storage_file))

        result_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_ened)

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported)

    def test_audit_logs_export_nonexistent(self):
        fake_path = os.path.join(self.test_dir.name, f"nonexistent_{uuid.uuid4()}.json")
        audit_exported = export_audit_logs(storage_file=fake_path)
        self.assertFalse(audit_exported)

if __name__ == "__main__":
    unittest.main()