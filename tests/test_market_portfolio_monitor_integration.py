import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs, MarketParser, MarketReportGenerator

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.telegram.org/bot{uuid.uuid4().hex}/sendMessage"
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_full_pipeline_and_edge_cases_integration(self):
        random_price = round(random.uniform(10.0, 5000.0), 4)
        
        # 1. Тест первичного запуска конвейера (start_new) на несуществующий/пустой файл
        result_start = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_start)
        self.assertTrue(os.path.exists(self.storage_file))

        # 2. Проверка через Parser и ReportGenerator реальных данных
        parser = MarketParser(storage_file=self.storage_file)
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        
        # Сохраняем случайное значение цены через fetch_and_store для проверки потока
        parser.fetch_and_store(symbol=self.symbol, price=random_price)
        
        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(str(random_price), report)
        self.assertIn(self.symbol, report)

        # 3. Тест алиаса start_ened с другим случайным значением
        new_random_price = round(random.uniform(5001.0, 10000.0), 4)
        parser.fetch_and_store(symbol=self.symbol, price=new_random_price)
        
        result_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_ened)

        # 4. Проверка экспорта аудиторских логов
        audit_valid = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_valid)

        # 5. Краевой случай: поврежденный JSON в хранилище (битый поток событий)
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{corrupted_json_stream_" + uuid.uuid4().hex)

        # Проверка реакции системы на битый файл (должна отрабатывать без падений)
        bad_load = parser.load_data(storage_file=self.storage_file)
        self.assertEqual(bad_load, {})

        audit_invalid = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(audit_invalid)

        # 6. Краевой случай: пустой файл
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        
        self.assertEqual(parser.load_data(storage_file=self.storage_file), {})
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

if __name__ == "__main__":
    unittest.main()