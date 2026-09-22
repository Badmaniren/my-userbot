import unittest
import os
import uuid
import random
from skills.market_report_generator import MarketReportGenerator, generate_market_report

class TestMarketReportGeneratorIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.random_suffix}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.test_price = round(random.uniform(10.0, 1000.0), 2)

        # Создаем начальный файл хранилища с реальными данными через модуль
        self.generator = MarketReportGenerator(self.storage_file)
        self.generator.parser.fetch_and_store(self.symbol, self.test_price)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_generate_symbol_report_integration(self):
        report = self.generator.generate_symbol_report(self.symbol)
        
        self.assertIsInstance(report, dict)
        self.assertIn(self.symbol, report)
        self.assertTrue(report[self.symbol])
        self.assertEqual(report.get('count'), 1)
        self.assertEqual(report.get('min_price'), self.test_price)
        self.assertEqual(report.get('max_price'), self.test_price)

    def test_update_and_fetch_report_integration(self):
        new_price = round(random.uniform(1001.0, 5000.0), 2)
        dummy_url = f"http://localhost/api/{uuid.uuid4().hex}"
        
        # Переопределяем метод fetch_price у встроенного парсера для возврата сгенерированного динамического значения
        self.generator.parser.fetch_price = lambda url: new_price
        
        fetched_price = self.generator.update_and_fetch_report(dummy_url, self.symbol)
        self.assertEqual(fetched_price, new_price)
        
        # Проверяем отчет после обновления
        updated_report = self.generator.generate_symbol_report(self.symbol)
        self.assertGreaterEqual(updated_report.get('count'), 2)
        self.assertEqual(updated_report.get('max_price'), new_price)

    def test_get_raw_stream_dump_integration(self):
        dump = self.generator.get_raw_stream_dump()
        self.assertIsNotNone(dump)
        if isinstance(dump, list):
            found = any(isinstance(item, dict) and item.get("symbol") == self.symbol for item in dump)
            self.assertTrue(found)
        elif isinstance(dump, dict):
            self.assertIn(self.symbol, dump)

    def test_generate_market_report_function_integration(self):
        result_str = generate_market_report(self.storage_file, self.symbol)
        self.assertIsInstance(result_str, str)
        self.assertIn(f"Report for {self.symbol}", result_str)
        self.assertIn(str(self.test_price), result_str)

if __name__ == "__main__":
    unittest.main()