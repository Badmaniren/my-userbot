import unittest
import os
import uuid
import random
from skills.market_report_generator import MarketReportGenerator, generate_market_report
from skills.market_parser import MarketParser
from skills import db_storage

class TestMarketReportGeneratorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.test_price = round(random.uniform(10.0, 500.0), 2)
        self.storage_file = f"test_market_data_{uuid.uuid4().hex}.json"
        
        # Очистка перед тестом, если файл существует
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def tearDown(self):
        # Удаление временного файла после тестов
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_market_report_pipeline_integration(self):
        # Инициализация реального парсера с временным файлом хранения
        parser = MarketParser(self.storage_file)
        
        # Реальный вызов метода сохранения через связанный навык (без моков)
        parser.fetch_and_store(self.test_symbol, self.test_price)
        
        # Проверяем, что файл действительно создан и содержит данные
        self.assertTrue(os.path.exists(self.storage_file))

        # Инициализация тестируемого модуля MarketReportGenerator с тем же файлом
        generator = MarketReportGenerator(self.storage_file)
        
        # Проверка генерации отчета по символу
        report = generator.generate_symbol_report(self.test_symbol)
        
        self.assertIn("count", report)
        self.assertEqual(report["count"], 1)
        self.assertEqual(report["min_price"], self.test_price)
        self.assertEqual(report["max_price"], self.test_price)
        self.assertTrue(report.get(self.test_symbol))

        # Проверка функции generate_market_report
        legacy_report = generate_market_report(self.storage_file, self.test_symbol)
        self.assertIn(self.test_symbol, legacy_report)
        self.assertIn(str(self.test_price), legacy_report)

        # Проверка получения сырого дампа
        raw_dump = generator.get_raw_stream_dump()
        self.assertIsNotNone(raw_dump)

    def test_market_report_no_data_handling(self):
        generator = MarketReportGenerator(self.storage_file)
        non_existent_symbol = f"NON_{uuid.uuid4().hex[:6].upper()}"
        
        report = generator.generate_symbol_report(non_existent_symbol)
        
        self.assertEqual(report.get("count"), 0)
        self.assertIn("error", report)

if __name__ == "__main__":
    unittest.main()