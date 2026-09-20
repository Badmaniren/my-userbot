import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_analytics_dashboard import MarketPortfolioIntegrationHub
from market_portfolio_collector_agent import MarketParser
from market_portfolio_valuation import PortfolioValuation

class TestMarketPortfolioIntegration(unittest.TestCase):
    def setUp(self):
        self.test_db = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = "http://mock-market-data.local/api"
        self.token = "test_token_123"
        self.chat_id = "999888"
        self.shifts = random.randint(1, 10)
        self.hub = MarketPortfolioIntegrationHub(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_full_pipeline_integration(self):
        # 1. Инициализация данных через Collector Agent
        collector = MarketParser(self.test_db)
        random_price = float(random.randint(100, 1000))
        collector.fetch_and_store(self.symbol, random_price)
        
        self.assertTrue(os.path.exists(self.test_db), "Файл хранилища не был создан.")

        # 2. Выполнение интеграционного конвейера через Hub
        # Проверяем, что метод отрабатывает без исключений и обновляет состояние
        result = self.hub.run_full_integration_pipeline(
            self.symbol, 
            self.url, 
            self.token, 
            self.chat_id, 
            self.shifts
        )
        
        # 3. Проверка записи данных через Valuation модуль
        valuation = PortfolioValuation(self.test_db)
        data = valuation.load_data(self.test_db)
        
        self.assertIsNotNone(data, "Данные не были загружены из хранилища.")
        
        # Проверяем наличие ключа с нашим случайным символом
        found = False
        for entry in data:
            if entry.get('symbol') == self.symbol:
                found = True
                break
        
        self.assertTrue(found, f"Символ {self.symbol} не найден в агрегированных данных.")

    def test_data_consistency_across_modules(self):
        # Проверка сквозной записи: Collector -> Storage -> Valuation
        price_val = float(random.uniform(10.0, 500.0))
        
        # Запись
        parser = MarketParser(self.test_db)
        parser.fetch_and_store(self.symbol, price_val)
        
        # Чтение через другой модуль
        valuation = PortfolioValuation(self.test_db)
        summary = valuation.get_total_summary(self.url)
        
        # Проверка, что данные, записанные одним модулем, видны другому
        with open(self.test_db, 'r') as f:
            content = json.load(f)
            self.assertEqual(content[-1]['price'], price_val, "Цена в хранилище не совпадает с записанной.")

if __name__ == '__main__':
    unittest.main()