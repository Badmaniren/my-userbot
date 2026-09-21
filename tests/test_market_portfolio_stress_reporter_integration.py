import unittest
import os
import uuid
import random
from unittest.mock import patch, MagicMock
from skills.market_portfolio_stress_reporter import StressReporter
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics
from skills.market_portfolio_telegram_notifier import start_new
from skills.market_parser import MarketParser

class TestMarketPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"TICKER_{random.randint(1000, 9999)}"
        self.telegram_token = "test_token_123"
        self.chat_id = "test_chat_456"
        
        # Инициализация парсера для создания данных
        self.parser = MarketParser(self.storage_file)
        self.parser.fetch_and_store(self.symbol, float(random.randint(100, 1000)))
        
        # Инициализация тестируемого модуля
        self.reporter = StressReporter(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_stress_reporting_integration_flow(self):
        # 1. Проверка аналитики (входные данные для репортера)
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        metrics = analytics.calculate_metrics(self.symbol)
        self.assertIsInstance(metrics, dict, "Аналитика должна возвращать словарь метрик")

        # 2. Запуск стресс-тестирования через репортер
        shifts = [random.uniform(-0.2, 0.2) for _ in range(3)]
        report_data = self.reporter.run_stress_reporting(self.symbol, shifts)
        
        self.assertIsNotNone(report_data, "Репортер должен вернуть данные отчета")
        
        # 3. Формирование сообщения
        message = f"Stress Report for {self.symbol}: {str(report_data)}"
        
        # 4. Отправка через Telegram-нотификатор (интеграция)
        with patch("skills.market_portfolio_telegram_notifier.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"ok": True}
            mock_post.return_value = mock_response

            success = start_new(self.telegram_token, self.chat_id, message)

            # Проверка: если метод вернул True, значит отправка прошла успешно
            self.assertTrue(success, "Telegram нотификатор должен вернуть True при успешной отправке")

    def test_data_consistency_after_simulation(self):
        # Проверка, что симуляция не портит данные в хранилище
        initial_data = self.parser.load_data(self.storage_file)
        self.reporter.simulate_single(self.symbol, random.uniform(0.01, 0.05))
        final_data = self.parser.load_data(self.storage_file)

        self.assertEqual(len(initial_data), len(final_data), "Количество записей не должно меняться при симуляции")

if __name__ == '__main__':
    unittest.main()
