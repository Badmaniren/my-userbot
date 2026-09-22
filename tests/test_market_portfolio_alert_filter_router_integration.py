import os
import unittest
import uuid
import random
import json
from skills.market_portfolio_alert_filter_router import AlertFilterRouter

class TestAlertFilterRouterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage_" + str(uuid.uuid4())
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"storage_{uuid.uuid4()}.json")
        
        # Генерируем случайные начальные данные для реального хранилища, чтобы избежать моков
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        initial_data = {
            self.symbol: [
                {"price": round(random.uniform(10.0, 100.0), 2), "timestamp": "2023-01-01T00:00:00"}
            ]
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        self.url = f"https://example.com/api/{uuid.uuid4()}"
        self.telegram_token = f"token_{uuid.uuid4()}"
        self.chat_id = str(random.randint(100000, 999999))
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH"])
        self.min_threshold = round(random.uniform(1.0, 5.0), 2)
        self.channels = ["telegram"]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_alert_filter_router_integration_flow(self):
        router = AlertFilterRouter(storage_file=self.storage_file)
        
        # Проверяем интеграционный вызов load_stream_data, который читает реальный файл
        stream_data = router.load_stream_data()
        self.assertIsNotNone(stream_data)

        # Выполняем комплексную маршрутизацию и фильтрацию без моков
        result = router.process_and_route(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertIsInstance(result, dict)
        self.assertIn("analytics_data", result)
        
        # Проверяем алиас метод
        routed_result = router.route_filtered_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )
        self.assertIsInstance(routed_result, dict)

if __name__ == "__main__":
    unittest.main()