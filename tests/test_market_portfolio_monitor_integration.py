import unittest
import os
import uuid
import random
from skills import market_portfolio_monitor
from skills import db_storage

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.mockmarket.io/{uuid.uuid4().hex[:8]}"
        self.telegram_token = f"bot{random.randint(100000, 999999)}:AAG{uuid.uuid4().hex[:15]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_integration_pipeline_and_storage(self):
        initial_price = round(random.uniform(10.0, 5000.0), 2)

        db_storage.save_data(self.storage_file, {self.symbol: initial_price})
        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен быть создан через db_storage")

        result = market_portfolio_monitor.start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(result, "Пайплайн мониторинга должен успешно отработать")

        alias_result = market_portfolio_monitor.start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(alias_result, "Алиас start_ened должен успешно вызывать пайплайн")

        audit_status = market_portfolio_monitor.export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_status, "Экспорт аудиторских логов должен подтвердить целостность данных")

if __name__ == "__main__":
    unittest.main()
