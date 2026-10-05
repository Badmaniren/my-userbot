import unittest
import os
import tempfile
import uuid
import random
from skills.market_portfolio_monitor import (
    start_ened,
    start_new,
    run_pipeline,
    MarketParser,
    MarketReportGenerator,
    export_audit_logs
)

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.market-liquidity-{uuid.uuid4().hex[:4]}.test/v1"
        self.telegram_token = f"bot{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:10]}"
        self.chat_id = f"@{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_integration_pipeline_and_storage_lifecycle(self):
        initial_price = round(random.uniform(10.0, 5000.0), 2)
        
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=initial_price)
        
        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен быть создан")
        
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], initial_price)

        new_price = round(initial_price * 1.05, 2)
        
        result_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_ened)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report_text = report_gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report_text)
        
        stream_dump = report_gen.get_raw_stream_dump()
        self.assertIn(self.symbol, stream_dump)

        audit_result = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_result, "Аудит-логи должны успешно подтвердить корректность хранилища")

        pipeline_result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(pipeline_result)

    def test_start_new_entrypoint_with_randomized_context(self):
        random_price = round(random.uniform(1.0, 100.0), 4)
        
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        status = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        
        self.assertTrue(status)
        
        final_data = parser.load_data(self.storage_file)
        self.assertEqual(final_data.get(self.symbol), random_price)
        self.assertTrue(export_audit_logs(storage_file=self.storage_file))

if __name__ == "__main__":
    unittest.main()