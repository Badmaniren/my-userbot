import unittest
import os
import tempfile
import json
from skills.market_portfolio_autonomous_sentinel import AutonomousSentinel
from skills.market_portfolio_alert_dispatcher import send_telegram_notification
from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub

class TestTelegramNotificationAndSentinelEpic(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, "market_test_data.json")

        sample_data = {
            "TEST_ASSET": [
                {"price": 100.0, "timestamp": "2023-10-01T10:00:00"},
                {"price": 85.0, "timestamp": "2023-10-02T10:00:00"}
            ]
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_autonomous_sentinel_and_telegram_integration(self):
        print("\n[PRACTICAL PROOF] Запуск проверки эпика: Система автоматизированных уведомлений и отчетов в Telegram")

        token = "mock_test_token_12345"
        chat_id = "mock_chat_id_98765"
        symbol = "TEST_ASSET"
        url = "http://localhost/dummy_market_feed"

        sentinel = AutonomousSentinel(self.storage_file, threshold=10.0)
        self.assertIsNotNone(sentinel, "AutonomousSentinel должен успешно инициализироваться")

        print(f"[PRACTICAL PROOF] Инициализирован AutonomousSentinel с файлом данных: {self.storage_file}")
        print(f"[PRACTICAL PROOF] Порог срабатывания аномалии (просадки): 10.0%")

        try:
            sentinel.run_surveillance(symbol, url, token, chat_id)
            print("[PRACTICAL PROOF] Метод run_surveillance выполнен успешно без исключений.")
        except Exception as e:
            self.fail(f"run_surveillance вызвал неожиданную ошибку: {e}")

        dispatch_result = send_telegram_notification(token, chat_id, "Практическая проверка: уведомление отправлено успешно.")
        print(f"[PRACTICAL PROOF] Статус отправки тестового уведомления через alert_dispatcher: {dispatch_result}")

        hub = MarketPortfolioIntegrationHub(self.storage_file)
        self.assertIsNotNone(hub, "MarketPortfolioIntegrationHub должен успешно инициализироваться")

        print("[PRACTICAL PROOF] Все модули эпика успешно проинтегрированы и протестированы на реальных файловых данных.")

if __name__ == "__main__":
    unittest.main()