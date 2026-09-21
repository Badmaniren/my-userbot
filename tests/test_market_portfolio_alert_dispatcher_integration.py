import unittest
import os
import uuid
import random
from skills import market_portfolio_alert_dispatcher
from skills import market_parser

class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.unique_id = str(uuid.uuid4())[:8]
        self.symbol = f"TICK_{self.unique_id}"
        self.storage_file = f"test_storage_{self.unique_id}.json"
        self.telegram_token = f"token_{self.unique_id}"
        self.chat_id = str(random.randint(10000, 99999))
        self.random_price = round(random.uniform(10.0, 1000.0), 2)
        
        # Создаем начальные данные через реальный парсер/хранилище, чтобы модулям было с чем работать
        parser = market_parser.MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(self.symbol, self.random_price)

        # Формируем валидный локальный URL или заглушку для файловой/сетевой системы
        self.url = f"file://{os.path.abspath(self.storage_file)}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_dispatch_portfolio_alerts_integration(self):
        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertIsInstance(result, dict)
        self.assertIn("summary", result)
        self.assertIn("pnl", result)
        self.assertEqual(result.get("status"), "dispatched")

        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен существовать после выполнения диспатчера")

    def test_process_stream_alert_integration(self):
        stream_data = market_portfolio_alert_dispatcher.process_stream_alert(self.unique_id)
        self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()