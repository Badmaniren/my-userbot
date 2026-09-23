import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, run_pipeline

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 5000.0), 2)
        self.chat_id = str(random.randint(100000, 999999))
        self.url = f"https://api.telegram.org/bot{uuid.uuid4().hex[:8]}/sendMessage"
        self.telegram_token = uuid.uuid4().hex
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_run_pipeline_and_start_new_integration(self):
        # Проверяем работу start_new (интеграционный вызов без моков между компонентами модуля)
        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        
        self.assertTrue(result, "Конвейер должен возвращать True при успешном выполнении.")

        # Проверяем реальное создание файла хранилища и запись данных парсером
        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен быть создан в процессе работы конвейера.")
        
        with open(self.storage_file, "r", encoding="utf-8") as f:
            stored_data = json.load(f)
            
        self.assertIn(self.symbol, stored_data, "Символ должен быть сохранен в хранилище данных.")

        # Проверяем повторный вызов run_pipeline с обновленной ценой через случайный генератор
        new_price = round(self.price * 1.05, 2)

        from skills.market_portfolio_monitor import MarketParser
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=new_price)

        pipeline_result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(pipeline_result)

        with open(self.storage_file, "r", encoding="utf-8") as f:
            updated_data = json.load(f)

        self.assertEqual(updated_data[self.symbol], new_price, "Цена в хранилище должна обновиться на актуальную.")

if __name__ == "__main__":
    unittest.main()