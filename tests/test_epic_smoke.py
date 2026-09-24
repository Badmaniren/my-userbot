import unittest
import os
import json
import tempfile
from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer
from skills.market_portfolio_telegram_command_center import start_new

class TestTelegramCommandCenterEpicPractical(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, "portfolio_storage.json")

        sample_data = {
            "AAPL": [
                {"price": 150.0, "timestamp": "2023-10-01T10:00:00"},
                {"price": 155.0, "timestamp": "2023-10-02T10:00:00"},
                {"price": 148.0, "timestamp": "2023-10-03T10:00:00"},
                {"price": 160.0, "timestamp": "2023-10-04T10:00:00"}
            ]
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_command_center_and_analytics_pipeline(self):
        print("\n=== ПРАКТИЧЕСКАЯ ПРОВЕРКА ЭПИКА: Telegram-центр управления инвестициями ===")

        hub = MarketPortfolioIntegrationHub(self.storage_file)
        analytics = PortfolioPerformanceAnalytics(self.storage_file)
        simulator = PortfolioScenarioSimulator(self.storage_file)
        optimizer = PortfolioStrategyOptimizer(self.storage_file)

        symbol = "AAPL"

        print(f"\n1. Загрузка и анализ метрик портфеля для актива: {symbol}")
        metrics = analytics.calculate_metrics(symbol)
        print(f"-> Рассчитанные метрики портфеля: {metrics}")
        self.assertIsInstance(metrics, dict)

        print("\n2. Симуляция стресс-сценария и оценка устойчивости стратегии")
        stress_result = simulator.run_stress_test(symbol, [5, 10, 15])
        print(f"-> Результаты стресс-теста: {stress_result}")

        optimization_result = optimizer.evaluate_resilience(symbol, [5, 10])
        print(f"-> Оценка устойчивости стратегии: {optimization_result}")

        print("\n3. Интеграция с Telegram-центром команд (симуляция отправки отчета)")
        fake_token = "mock_telegram_bot_token_12345"
        fake_chat_id = "987654321"
        command_report_message = (
            f"🚀 [Command Center Report]\n"
            f"Asset: {symbol}\n"
            f"Metrics: {metrics}\n"
            f"Stress Test Status: Executed successfully."
        )

        dispatch_result = start_new(fake_token, fake_chat_id, command_report_message)
        print(f"-> Статус отправки отчета через Telegram API: {dispatch_result}")
        self.assertTrue(dispatch_result)

        print("\n=== ВСЕ ПРАКТИЧЕСКИЕ ПРОВЕРКИ ЭПИКА УСПЕШНО ПРОШЛИ ===")

if __name__ == "__main__":
    unittest.main()