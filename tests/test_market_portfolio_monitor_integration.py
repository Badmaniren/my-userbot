import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_ened, export_audit_logs, MarketParser

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.test_url = f"https://api.test.local/v1/{uuid.uuid4().hex[:4]}"
        self.test_token = f"tok_{uuid.uuid4().hex[:8]}"
        self.test_chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.test_price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_portfolio_monitor_full_pipeline_integration(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.test_symbol, price=self.test_price)
        
        pipeline_result = start_ened(
            symbol=self.test_symbol,
            url=self.test_url,
            telegram_token=self.test_token,
            chat_id=self.test_chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(pipeline_result, "Конвейер мониторинга портфеля должен успешно завершиться")
        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен быть создан в процессе работы конвейера")

        with open(self.storage_file, "r", encoding="utf-8") as f:
            stored_data = json.load(f)
        
        self.assertIn(self.test_symbol, stored_data, "Символ должен присутствовать в данных хранилища")
        
        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported, "Экспорт аудиторских логов должен подтвердить наличие данных")

if __name__ == "__main__":
    unittest.main()