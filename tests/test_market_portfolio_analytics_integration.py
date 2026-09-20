import unittest
import os
import tempfile
import uuid
import random
from skills.market_portfolio_analytics import PortfolioAnalytics
from skills.db_storage import MarketParser
from skills.market_report_generator import MarketReportGenerator

class TestMarketPortfolioAnalyticsIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4()}.json")
        
        self.symbol = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.prices = [round(random.uniform(100.0, 500.0), 2) for _ in range(5)]
        
        parser = MarketParser(self.storage_file)
        for p in self.prices:
            parser.fetch_and_store(self.symbol, p)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_portfolio_analytics_integration(self):
        self.assertTrue(os.path.exists(self.storage_file), "Хранилище данных не было создано")
        
        report_gen = MarketReportGenerator(self.storage_file)
        report = report_gen.generate_symbol_report(self.symbol)
        
        self.assertIsNotNone(report, "Отчет по символу не сгенерирован")
        
        analytics = PortfolioAnalytics(self.storage_file)
        metrics = analytics.calculate_metrics(self.symbol)
        
        self.assertIsInstance(metrics, dict, "Метрики портфеля должны быть возвращены в виде словаря")
        self.assertIn("return", metrics, "В метриках отсутствует расчет доходности (return)")
        
        expected_min = min(self.prices)
        expected_max = max(self.prices)
        
        dump = report_gen.get_raw_stream_dump()
        self.assertIn(self.symbol, str(dump), "Дамп потока не содержит тестируемый символ")

if __name__ == "__main__":
    unittest.main()