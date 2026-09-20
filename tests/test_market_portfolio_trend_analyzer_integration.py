import unittest
import os
import uuid
import random
from skills.market_portfolio_trend_analyzer import analyze_trend, PortfolioTrendAnalyzer
from skills.market_portfolio_monitor import run_pipeline as monitor_pipeline
from skills.market_portfolio_valuation import PortfolioValuation

class TestMarketPortfolioTrendAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.symbol = f"TEST_{random.randint(1000, 9999)}_{self.random_suffix}"
        self.storage_file = f"test_market_data_{self.random_suffix}.json"
        self.url = f"http://example.com/api/{self.random_suffix}"
        self.chat_id = str(random.randint(100000, 999999))
        self.telegram_token = f"fake_token_{self.random_suffix}"
        self.initial_price = round(random.uniform(10.0, 500.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_trend_analyzer_composition_integration(self):
        monitor_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен быть создан мониторингом.")

        valuation_module = PortfolioValuation(self.storage_file)
        valuation_data = valuation_module.evaluate_portfolio(self.url)
        self.assertIsNotNone(valuation_data, "Оценка портфеля не должна быть пустой.")

        trend_result = analyze_trend(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url
        )

        self.assertIsNotNone(trend_result, "Результат анализа тренда не должен быть пустым.")

        analyzer_class_instance = PortfolioTrendAnalyzer(self.storage_file)
        class_trend_result = analyzer_class_instance.analyze(self.symbol, self.url)

        self.assertIsInstance(class_trend_result, dict, "Анализ через класс должен возвращать словарь.")
        self.assertIn("trend", class_trend_result, "Результат должен содержать ключ тренда.")

if __name__ == "__main__":
    unittest.main()