import unittest
import os
import uuid
import random
from skills.market_portfolio_rebalancer import *
from skills.market_parser import MarketParser
from skills.market_portfolio_valuation import PortfolioValuation

class TestMarketPortfolioRebalancerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = "test_data_integration"
        os.makedirs(self.test_dir, exist_ok=True)

        self.unique_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        self.test_url = f"http://example.com/market/{uuid.uuid4().hex}"

        self.random_price = round(random.uniform(10.0, 1000.0), 2)

        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.unique_symbol, self.random_price)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_rebalancer_integration_with_valuation_and_parser(self):
        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен быть создан парсером")

        parser = MarketParser(self.storage_file)
        loaded_data = parser.load_data(self.storage_file)
        self.assertIn(self.unique_symbol, str(loaded_data), "Сохраненный символ должен присутствовать в хранилище")

        valuation = PortfolioValuation(self.storage_file)
        valuation_data = valuation.load_data(self.storage_file)
        self.assertIsNotNone(valuation_data, "Модуль оценки портфеля должен успешно загрузить данные из хранилища")

        rebalancer_result = calculate_optimal_proportions(self.storage_file, self.unique_symbol)

        self.assertIsNotNone(rebalancer_result, "Интеграционный расчет пропорций не должен возвращать None")

        if isinstance(rebalancer_result, dict):
            self.assertGreater(len(rebalancer_result), 0, "Результат ребалансировки не должен быть пустым словарем")
        elif isinstance(rebalancer_result, (list, tuple)):
            self.assertGreater(len(rebalancer_result), 0, "Результат ребалансировки не должен быть пустым списком")
        else:
            self.assertTrue(hasattr(rebalancer_result, '__dict__') or rebalancer_result, "Результат должен содержать валидные данные")

if __name__ == '__main__':
    unittest.main()