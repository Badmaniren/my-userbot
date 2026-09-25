import unittest
import uuid
import random
import os
from skills.market_insider_activity_tracker import MarketInsiderActivityTrackerModuleAPI
from db_storage import DBStorage  # Предполагаемый интерфейс БД из сигнатур

class TestMarketInsiderActivityTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.api = MarketInsiderActivityTrackerModuleAPI()
        self.db = DBStorage(db_path="test_integration.db")
        self.ticker_id = f"TICKER_{uuid.uuid4().hex[:8].upper()}"

    def tearDown(self):
        if os.path.exists("test_integration.db"):
            os.remove("test_integration.db")

    def test_full_activity_tracking_lifecycle(self):
        # Генерируем случайные данные для исключения хардкода
        random_volume = random.uniform(1000.0, 1000000.0)
        random_multiplier = random.uniform(0.5, 10.0)
        
        payload = {
            "ticker_id": self.ticker_id,
            "volume": random_volume,
            "anomaly_multiplier": random_multiplier
        }

        # Вызов модуля
        result = self.api.track_activity(payload)

        # Валидация структуры ответа
        self.assertIn("anomaly_detected", result)
        self.assertEqual(result["ticker_id"], self.ticker_id)
        self.assertIsInstance(result["signature"], str)
        self.assertTrue(len(result["signature"]) > 0)

        # Интеграция с БД: запись результата
        self.db.save_activity(
            ticker=result["ticker_id"],
            is_anomaly=result["anomaly_detected"],
            signature=result["signature"]
        )

        # Проверка сохранения в реальной БД
        stored_record = self.db.get_last_activity(self.ticker_id)
        
        self.assertIsNotNone(stored_record, "Запись не найдена в БД")
        self.assertEqual(stored_record["signature"], result["signature"])
        self.assertEqual(stored_record["ticker"], self.ticker_id)
        
        # Проверка логики аномалии
        expected_anomaly = random_volume > 500000.0 or random_multiplier > 5.0
        self.assertEqual(result["anomaly_detected"], expected_anomaly)

    def test_invalid_input_resilience(self):
        # Проверка устойчивости к мусорным данным без подавления исключений
        bad_payload = {
            "ticker_id": "INVALID",
            "volume": "not_a_number",
            "anomaly_multiplier": None
        }
        
        result = self.api.track_activity(bad_payload)
        
        # Проверка, что система корректно обработала типы (volume=0.0, multiplier=1.0)
        self.assertEqual(result["volume"], 0.0)
        self.assertFalse(result["anomaly_detected"])
        self.assertIsInstance(result["signature"], str)

if __name__ == "__main__":
    unittest.main()