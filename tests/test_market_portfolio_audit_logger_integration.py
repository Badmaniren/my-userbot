import os
import unittest
import uuid
import random
from skills.market_portfolio_audit_logger import MarketPortfolioAuditLogger
from skills.db_storage import MarketParser

class TestMarketPortfolioAuditLoggerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_storage_{self.test_id}.json"
        self.audit_file = f"audit_log_{self.test_id}.json"
        self.symbol = f"TICKER_{self.test_id}"
        self.initial_price = round(random.uniform(10.0, 1000.0), 2)

        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.initial_price)

    def tearDown(self):
        for filename in [self.storage_file, self.audit_file]:
            if os.path.exists(filename):
                os.remove(filename)

    def test_audit_logger_integration(self):
        audit_logger = MarketPortfolioAuditLogger(self.storage_file)

        self.assertTrue(
            hasattr(audit_logger, 'run_audit_and_export'),
            "Модуль MarketPortfolioAuditLogger должен содержать метод run_audit_and_export"
        )

        result = audit_logger.run_audit_and_export(self.symbol, self.audit_file)

        self.assertTrue(
            os.path.exists(self.audit_file),
            f"Интеграционный тест не обнаружил созданный файл аудита: {self.audit_file}"
        )

        self.assertIsInstance(
            result,
            (dict, list),
            "Метод аудита должен возвращать структурированные данные (dict или list)"
        )

if __name__ == "__main__":
    unittest.main()