import unittest
import uuid
import random
import os
import tempfile
from typing import Dict, Any

from skills.market_insider_alert_pipeline import (
    MarketInsiderAlertPipeline,
    process_insider_alert_pipeline
)
from skills.market_insider_activity_tracker import MarketInsiderActivityTracker, DBStorage
from skills.market_portfolio_alert_dispatcher import dispatch_portfolio_alerts


class TestMarketInsiderAlertPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)

        self.storage_fd, self.storage_file = tempfile.mkstemp(suffix=".json")
        os.close(self.storage_fd)

        self.ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.volume = random.randint(10000, 500000)
        self.price = round(random.uniform(10.0, 1000.0), 2)

        self.raw_data_stream = {
            "ticker": self.ticker,
            "volume": self.volume,
            "price": self.price,
            "insider_action": "BUY",
            "anomaly_score": round(random.uniform(0.8, 1.0), 2)
        }

        self.telegram_token = f"test_token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.url = f"https://api.example.com/portfolio/{uuid.uuid4().hex}"

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_insider_alert_pipeline_composition(self):
        pipeline = MarketInsiderAlertPipeline(
            db_path=self.db_path,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        result = pipeline.process_stream(self.raw_data_stream)

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result.get("ticker"), self.ticker)

        storage = DBStorage(db_path=self.db_path)
        last_activity = storage.get_last_activity(self.ticker)

        self.assertIsNotNone(last_activity, "Данные инсайдерской активности должны быть сохранены в БД через трекер")
        self.assertEqual(last_activity.get("ticker"), self.ticker)

        self.assertTrue(
            os.path.exists(self.storage_file),
            "Диспетчер алертов должен инициировать или обновить файл хранилища портфеля"
        )

    def test_functional_pipeline_wrapper(self):
        config = {
            "db_path": self.db_path,
            "telegram_token": self.telegram_token,
            "chat_id": self.chat_id,
            "storage_file": self.storage_file,
            "severity_level": "CRITICAL",
            "min_threshold": random.randint(1000, 5000),
            "channels": ["telegram"]
        }

        response = process_insider_alert_pipeline(self.raw_data_stream, config)

        self.assertIsInstance(response, dict)
        self.assertIn("processed", response)
        self.assertTrue(response["processed"])

        storage = DBStorage(db_path=self.db_path)
        activity = storage.get_last_activity(self.ticker)
        self.assertIsNotNone(activity)


if __name__ == "__main__":
    unittest.main()