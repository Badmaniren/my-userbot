import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, MarketParser, MarketReportGenerator

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_id = str(uuid.uuid4())[:8]
        self.symbol = f"COIN_{self.test_id}"
        self.storage_file = f"test_storage_{self.test_id}.json"
        self.url = f"https://example.com/api/{self.test_id}"
        self.telegram_token = f"token_{self.test_id}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_pipeline_integration_flow(self):
        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен быть создан в процессе выполнения пайплайна")

        parser = MarketParser(storage_file=self.storage_file)
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)

        reporter = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = reporter.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, symbol_report)

        raw_dump = reporter.get_raw_stream_dump()
        self.assertIsInstance(raw_dump, str)
        parsed_dump = json.loads(raw_dump)
        self.assertIn(self.symbol, parsed_dump)

if __name__ == "__main__":
    unittest.main()