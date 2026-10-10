import unittest
import os
import uuid
import random
from skills.market_portfolio_stream_alert_bridge import (
    process_stream_and_dispatch_alert
)

class TestMarketPortfolioStreamAlertBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = str(uuid.uuid4())
        self.symbol = f"TEST_{random.randint(1000, 9999)}"
        self.stream_source = f"wss://stream.integration.test/{self.symbol}"
        self.output_path = f"test_stream_output_{self.unique_id}.json"
        self.storage_file = f"test_storage_{self.unique_id}.json"
        self.telegram_token = f"token_{random.randint(100000, 999999)}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.price_jump = round(random.uniform(5.0, 50.0), 2)
        
        self.payload = {
            "event_id": self.unique_id,
            "symbol": self.symbol,
            "price_delta": self.price_jump,
            "timestamp": random.randint(1600000000, 1700000000)
        }

    def tearDown(self):
        for path in [self.output_path, self.storage_file]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_stream_ingest_and_alert_dispatch_composition(self):
        context = {
            "run_id": self.unique_id,
            "mode": "integration_test"
        }
        
        result = process_stream_and_dispatch_alert(
            context=context,
            stream_source=self.stream_source,
            payload=self.payload,
            output_path=self.output_path,
            url=f"https://api.integration.test/alert/{self.unique_id}",
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level="HIGH",
            min_threshold=self.price_jump - 1.0,
            channels=["telegram", "webhook"]
        )

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result.get("event_id"), self.unique_id)
        
        self.assertTrue(
            os.path.exists(self.output_path),
            f"Ожидается создание файла вывода потока: {self.output_path}"
        )
        
        self.assertTrue(
            os.path.exists(self.storage_file) or result.get("dispatched") is True,
            "Интеграционный модуль должен выполнить диспетчеризацию алертов через связанные навыки"
        )

if __name__ == "__main__":
    unittest.main()