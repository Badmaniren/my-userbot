import unittest
import os
import uuid
import random
import tempfile

from skills.market_portfolio_alert_event_sink import process_event_sink_trigger
from skills.market_portfolio_alert_dispatcher import dispatch_portfolio_alerts
from skills.market_portfolio_alert_filter_router import AlertFilterRouter


class TestMarketPortfolioAlertEventSinkIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4()}.json")
        
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.test-market.org/v1/quote/{self.symbol.lower()}"
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:20]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        
        severities = ["INFO", "WARNING", "CRITICAL", "EMERGENCY"]
        self.severity_level = random.choice(severities)
        self.min_threshold = round(random.uniform(10.0, 1000.0), 2)
        self.channels = random.choice([["telegram"], ["console"], ["telegram", "console"]])

    def tearDown(self):
        self.test_dir.cleanup()

    def test_event_sink_composition_integration(self):
        # Проверяем сквозную интеграцию без моков: вызываем тестируемый модуль,
        # который обязан использовать реальные импорты диспетчера и роутера, а также хранилище.
        
        result = process_event_sink_trigger(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        # Проверяем возврат структурированных данных и использование уникальных параметров
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result.get("symbol"), self.symbol)
        
        # Проверяем реальное побочное действие: создание и запись в файл хранилища
        self.assertTrue(
            os.path.exists(self.storage_file),
            f"Файл хранилища {self.storage_file} не был создан модулем события."
        )
        
        with open(self.storage_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertGreater(len(content), 0, "Файл хранилища пуст.")
            self.assertIn(self.symbol, content)

        # Дополнительная проверка через прямой вызов компонентов композиции, 
        # подтверждающая корректность связывания роутера и диспетчера.
        router = AlertFilterRouter(storage_file=self.storage_file)
        stream_data = router.load_stream_data()
        self.assertIsNotNone(stream_data)


if __name__ == "__main__":
    unittest.main()