import unittest
import uuid
import random
import os
import sys
from skills.market_insider_event_extractor import MarketInsiderEventExtractor
try:
    from db_storage import DBStorage
    from market_portfolio_event_intelligence_hub import MarketPortfolioEventIntelligenceHub
except ImportError:
    from skills.db_storage import DBStorage
    from skills.market_portfolio_event_intelligence_hub import MarketPortfolioEventIntelligenceHub

class TestMarketInsiderEventExtractorIntegration(unittest.TestCase):
    def setUp(self):
        """Инициализация реальных компонентов без моков"""
        self.storage = DBStorage()
        self.event_hub = MarketPortfolioEventIntelligenceHub()
        self.extractor = MarketInsiderEventExtractor(
            storage=self.storage,
            hub=self.event_hub
        )

    def test_full_extraction_and_storage_flow(self):
        """Проверка полного цикла: запрос -> парсинг -> сохранение -> уведомление"""

        # Генерируем случайные входные данные для исключения кэширования и заглушек
        random_id = str(uuid.uuid4())
        test_tickers = ["AAPL", "TSLA", "MSFT", "NVDA", "AMZN"]
        selected_ticker = random.choice(test_tickers)
        unique_tag = f"test_run_{random.randint(1000, 9999)}"

        # Выполняем извлечение данных
        # Метод должен использовать requests и BeautifulSoup4 внутри
        extraction_result = self.extractor.extract_and_sync(
            ticker=selected_ticker,
            request_id=random_id,
            metadata={"tag": unique_tag}
        )

        # 1. Проверка структуры возвращаемого ответа
        self.assertIsInstance(extraction_result, dict)
        self.assertEqual(extraction_result["request_id"], random_id)
        self.assertIn("events_count", extraction_result)

        # 2. Проверка реального изменения в db_storage
        # Экстрактор обязан сохранить результаты в базу данных
        persisted_data = self.storage.get_insider_trades_by_request(random_id)
        self.assertIsNotNone(persisted_data, "Данные должны быть физически сохранены в DBStorage")

        if extraction_result["events_count"] > 0:
            self.assertGreater(len(persisted_data), 0)
            self.assertEqual(persisted_data[0]["ticker"], selected_ticker)

        # 3. Проверка интеграции с Intelligence Hub
        # После парсинга экстрактор должен отправить событие в хаб для анализа аномалий
        hub_events = self.event_hub.get_recent_events(source="market_insider_event_extractor")
        matching_event = next((e for e in hub_events if e.get("correlation_id") == random_id), None)

        self.assertIsNotNone(matching_event, "Событие должно быть передано в MarketPortfolioEventIntelligenceHub")
        self.assertEqual(matching_event["status"], "DATA_EXTRACTED")

    def test_extraction_error_handling_integration(self):
        """Проверка интеграции при некорректных данных (несуществующий тикер)"""
        invalid_ticker = f"NONEXISTENT_{uuid.uuid4().hex[:8]}"
        error_trace_id = str(uuid.uuid4())

        # Запуск с заведомо ложным тикером
        result = self.extractor.extract_and_sync(
            ticker=invalid_ticker,
            request_id=error_trace_id
        )

        # Проверяем, что система корректно обработала пустой результат парсинга BS4
        self.assertEqual(result["events_count"], 0)

        # Проверяем, что в логах аудита (через storage) зафиксирована попытка
        audit_log = self.storage.get_audit_log(operation_id=error_trace_id)
        self.assertIsNotNone(audit_log)

if __name__ == "__main__":
    unittest.main()