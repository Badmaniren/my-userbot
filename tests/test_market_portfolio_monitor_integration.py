import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, MarketParser, MarketReportGenerator

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 1500.0), 2)
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.telegram_token = f"token_{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_full_pipeline_integration(self):
        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        
        self.assertTrue(result, "Пipeline должен возвращать True при успешном выполнении.")
        
        self.assertTrue(
            os.path.exists(self.storage_file), 
            "Файл хранилища должен быть создан в процессе работы конвейера."
        )

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertIsInstance(data, dict, "Данные в хранилище должны быть словарем.")
        self.assertIn(self.symbol, data, f"Символ {self.symbol} должен присутствовать в хранилище.")
        
        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report = report_gen.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report, "Отчет должен содержать наименование символа.")
        
        stream_dump = report_gen.get_raw_stream_dump()
        self.assertIn(self.symbol, stream_dump, "Дамп потока должен отражать сохраненные данные.")

if __name__ == "__main__":
    unittest.main()