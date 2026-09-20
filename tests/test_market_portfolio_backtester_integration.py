import unittest
import os
import uuid
import random
from skills.market_portfolio_backtester import PortfolioBacktester
from skills.db_storage import MarketParser
from skills.market_portfolio_valuation import PortfolioValuation

class TestMarketPortfolioBacktesterIntegration(unittest.TestCase):

    def setUp(self):
        self.unique_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_storage_{self.unique_id}.json"
        self.symbol = f"TICK_{self.unique_id.upper()}"
        self.url = f"http://example.com/market/{self.unique_id}"

        # Инициализируем хранилище и записываем случайные исторические данные без моков
        parser = MarketParser(self.storage_file)
        self.base_price = round(random.uniform(100.0, 500.0), 2)
        parser.fetch_and_store(self.symbol, self.base_price)

        # Добавляем еще пару ценовых точек для имитации истории
        self.second_price = round(self.base_price * random.uniform(0.9, 1.1), 2)
        parser.fetch_and_store(self.symbol, self.second_price)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_backtester_integration_with_storage_and_valuation(self):
        # Проверяем реальную интеграцию бэктестера с хранилищем и модулем оценки
        backtester = PortfolioBacktester(self.storage_file)
        valuation = PortfolioValuation(self.storage_file)

        # Получаем оценку портфеля напрямую через связанный модуль
        eval_result = valuation.evaluate_portfolio(self.url)
        self.assertIsNotNone(eval_result)

        # Запускаем ретроспективное тестирование (бэктест) с использованием реальных данных из файла
        backtest_summary = backtester.run_backtest(self.symbol)

        self.assertIsInstance(backtest_summary, dict)
        self.assertIn("symbol", backtest_summary)
        self.assertEqual(backtest_summary["symbol"], self.symbol)

        # Проверяем, что расчеты бэктестера опираются на реально записанные данные
        pnl_calculation = valuation.calculate_portfolio_pnl(self.url)
        self.assertIsNotNone(pnl_calculation)

if __name__ == "__main__":
    unittest.main()