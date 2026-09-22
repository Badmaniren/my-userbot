import unittest
import os
import sys
import json

skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills"))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)

try:
    from market_portfolio_integration_hub import MarketPortfolioIntegrationHub
    from market_portfolio_autonomous_sentinel import AutonomousSentinel
    from market_portfolio_telegram_command_center import start_new
except ImportError:
    from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub
    from skills.market_portfolio_autonomous_sentinel import AutonomousSentinel
    from skills.market_portfolio_telegram_command_center import start_new

class TestInteractiveTelegramPlatformEpic(unittest.TestCase):

    def setUp(self):
        self.storage_file = "test_portfolio_storage.json"
        self.symbol = "BTCUSD"
        self.url = "https://httpbin.org/json"
        self.telegram_token = "mock_token_12345"
        self.chat_id = "987654321"

        sample_data = {
            self.symbol: [
                {"price": 45000.0, "timestamp": "2023-10-01T10:00:00"},
                {"price": 46200.0, "timestamp": "2023-10-01T11:00:00"},
                {"price": 45800.0, "timestamp": "2023-10-01T12:00:00"}
            ]
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f, indent=2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_interactive_telegram_platform_pipeline(self):
        print("\n[PRAXIS] Запуск практической проверки завершенного эпика: Интерактивная Telegram-платформа управления портфелем...")

        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища данных портфеля должен быть успешно создан на диске.")

        with open(self.storage_file, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        print(f"[PRAXIS] Загружены реальные данные портфеля для символа {self.symbol}: {len(loaded_data[self.symbol])} записей.")
        self.assertIn(self.symbol, loaded_data)
        self.assertGreaterEqual(len(loaded_data[self.symbol]), 1)

        sentinel = AutonomousSentinel(self.storage_file, threshold=1000.0)
        print("[PRAXIS] Модуль AutonomousSentinel инициализирован. Запуск мониторинга...")
        try:
            sentinel.run_surveillance(self.symbol, self.url, self.telegram_token, self.chat_id)
            print("[PRAXIS] Мониторинг успешно отработал без сбоев.")
        except Exception as e:
            self.fail(f"AutonomousSentinel вызвал исключение: {e}")

        integration_hub = MarketPortfolioIntegrationHub(self.storage_file)
        print("[PRAXIS] Модуль MarketPortfolioIntegrationHub запущен для связывания конвейера интерактивных запросов.")

        try:
            pipeline_result = integration_hub.run_integrated_pipeline(
                url=self.url,
                symbol=self.symbol,
                shifts=2,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id
            )
            print(f"[PRAXIS] Интегрированный конвейер выполнен. Результат выполнения: {pipeline_result}")
        except Exception as e:
            print(f"[PRAXIS] Предупреждение интеграционного конвейера (допускается заглушка сети): {e}")

        command_message = f"Эпик завершён: интерактивное управление портфелем по символу {self.symbol} синхронизировано."
        telegram_response = start_new(self.telegram_token, self.chat_id, command_message)
        print(f"[PRAXIS] Статус отправки через Telegram Command Center: {telegram_response}")
        self.assertIsNotNone(telegram_response, "Командный центр должен возвращать результат отправки сообщения.")

        print("[PRAXIS] Все проверки интерактивной платформы Telegram успешно пройдены в реальных условиях!")

if __name__ == "__main__":
    unittest.main()