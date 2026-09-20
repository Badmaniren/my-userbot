import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_tracker import MarketParser, MarketReportGenerator, run_market_telegram_pipeline

class TestMarketPortfolioIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.storage_file = f"test_storage_{self.test_id}.json"
        self.symbol = f"TICKER_{random.randint(1000, 9999)}"
        self.price = round(random.uniform(10.0, 500.0), 2)
        self.url = "http://mock-market-data.local"
        self.telegram_token = "test_token_123"
        self.chat_id = "987654321"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_full_market_pipeline_integration(self):
        # 1. Инициализация хранилища через MarketParser
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        
        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища не был создан")
        
        # 2. Проверка корректности записи через загрузку данных
        data = parser.load_data(self.storage_file)
        self.assertIn(self.symbol, data, "Символ не найден в хранилище")
        self.assertEqual(data[self.symbol], self.price, "Цена в хранилище не совпадает с записанной")

        # 3. Генерация отчета через MarketReportGenerator
        generator = MarketReportGenerator(self.storage_file)
        report = generator.generate_symbol_report(self.symbol)
        
        self.assertIsNotNone(report, "Отчет не был сгенерирован")
        self.assertIn(str(self.price), str(report), "Отчет не содержит актуальную цену")

        # 4. Проверка пайплайна (интеграция с Telegram-логикой)
        # Вызываем функцию, которая связывает все модули воедино
        result = run_market_telegram_pipeline(
            self.storage_file, 
            self.symbol, 
            self.chat_id, 
            self.url, 
            self.telegram_token
        )
        
        # Проверяем, что пайплайн отработал без исключений и вернул статус
        self.assertIsNotNone(result, "Пайплайн не вернул результат выполнения")

    def test_data_consistency_across_modules(self):
        # Проверка целостности данных при множественных записях
        parser = MarketParser(self.storage_file)
        new_price = round(random.uniform(500.0, 1000.0), 2)
        
        parser.fetch_and_store(self.symbol, new_price)
        
        generator = MarketReportGenerator(self.storage_file)
        raw_dump = generator.get_raw_stream_dump()
        
        self.assertEqual(raw_dump[self.symbol], new_price, "Данные в дампе не соответствуют последнему обновлению")

if __name__ == '__main__':
    unittest.main()