import unittest
import uuid
import random
from skills.market_insider_notifier import MarketInsiderNotifier
from skills.market_insider_alert_pipeline import MarketInsiderAlertPipeline
from skills.market_portfolio_telegram_notifier import send_telegram_notification

class TestMarketInsiderNotifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.test_token = "TEST_BOT_TOKEN"
        self.test_chat_id = "123456789"
        self.criticality_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        
        self.pipeline = MarketInsiderAlertPipeline()
        self.notifier = MarketInsiderNotifier(
            pipeline=self.pipeline,
            telegram_sender=send_telegram_notification
        )

    def test_end_to_end_anomaly_notification_flow(self):
        # Генерируем случайные данные для имитации рыночной аномалии
        anomaly_id = str(uuid.uuid4())
        raw_data = {
            "id": anomaly_id,
            "price_change": random.uniform(5.0, 25.0),
            "volume_spike": random.choice([True, False]),
            "timestamp": random.randint(1600000000, 1700000000)
        }
        
        # Выбираем случайный уровень критичности для фильтрации
        target_level = random.choice(self.criticality_levels)
        
        # Выполняем интеграционный вызов:
        # 1. Pipeline обрабатывает поток данных
        # 2. Notifier фильтрует и отправляет через Telegram
        result = self.notifier.process_and_notify(
            ticker=self.test_ticker,
            raw_stream_data=raw_data,
            min_criticality=target_level,
            token=self.test_token,
            chat_id=self.test_chat_id
        )
        
        # Проверяем, что процесс завершился успешно
        self.assertTrue(result, "Notifier failed to process and dispatch the alert.")
        
        # Проверяем, что данные были корректно переданы в pipeline
        # (Проверка через состояние объекта, если pipeline сохраняет последнее состояние)
        processed_data = self.pipeline.process_alert_stream(self.test_ticker, raw_data)
        self.assertIsNotNone(processed_data, "Pipeline failed to process the generated anomaly data.")
        
        # Проверяем, что Telegram-нотификатор вернул True (успешная отправка)
        # Используем реальный вызов функции, как того требует интеграционный тест
        telegram_status = send_telegram_notification(
            token=self.test_token,
            chat_id=self.test_chat_id,
            message=f"Alert for {self.test_ticker}: {anomaly_id} with level {target_level}"
        )
        self.assertTrue(telegram_status, "Telegram notifier failed to send the message.")

    def test_filtering_logic_integrity(self):
        # Проверка того, что фильтрация работает: 
        # если уровень ниже требуемого, нотификация не должна уходить
        low_level_data = {"id": str(uuid.uuid4()), "severity": "LOW"}
        
        # Попытка отправить с фильтром CRITICAL
        result = self.notifier.process_and_notify(
            ticker=self.test_ticker,
            raw_stream_data=low_level_data,
            min_criticality="CRITICAL",
            token=self.test_token,
            chat_id=self.test_chat_id
        )
        
        # Ожидаем False, так как фильтр отсек данные
        self.assertFalse(result, "Notifier allowed low-criticality data through strict filter.")

if __name__ == '__main__':
    unittest.main()