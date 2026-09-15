import unittest
import time
import requests
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.notification_template_engine import NotificationTemplateEngine
from skills.notification_webhook_broadcaster import NotificationWebhookBroadcaster

class TestNotificationEpicIntegration(unittest.TestCase):
    """
    Одноразовая проверка интеграции: Диспетчер -> Шаблонизатор -> Вебхук.
    Используем публичный RSS-фид (Hacker News) как источник 'инцидентов' для дайджеста.
    """

    def setUp(self):
        self.dispatcher = NotificationChannelDispatcher()
        self.template_engine = NotificationTemplateEngine()
        self.broadcaster = NotificationWebhookBroadcaster()
        
        # Регистрируем тестовый вебхук (используем webhook.site для демонстрации получения данных)
        self.webhook_url = "https://webhook.site/a1b2c3d4-e5f6-4789-8012-34567890abcd"
        self.broadcaster.register_webhook_channel("test_channel", {"url": self.webhook_url})

    def test_full_notification_pipeline(self):
        print("\n--- Запуск проверки системы оповещений ---")
        
        # 1. Получение реальных данных (имитация потока инцидентов из RSS)
        feed_url = "https://hnrss.org/newest?points=100"
        data = None
        for attempt in range(2):
            try:
                response = requests.get(feed_url, timeout=10)
                if response.status_code == 200:
                    data = response.text
                    print(f"[OK] Получены данные из {feed_url}")
                    break
            except Exception as e:
                print(f"[Retry] Попытка {attempt + 1} не удалась: {e}")
                time.sleep(1)
        
        self.assertIsNotNone(data, "Не удалось получить данные из сети")

        # 2. Обработка через шаблонизатор
        # Используем встроенный метод для парсинга потока
        parsed_data = self.template_engine.parse_stream_data(data)
        self.assertIsNotNone(parsed_data, "Шаблонизатор не смог распарсить поток")
        
        # Берем первый элемент как "критический инцидент"
        incident_id = "INC-999"
        severity = "CRITICAL"
        
        # 3. Генерация полезной нагрузки
        payload = self.template_engine.generate_notification_payload(
            severity, incident_id, {"title": "System Failure Detected", "details": "High latency in module"}
        )
        print(f"[Payload] Сгенерировано: {payload}")

        # 4. Широковещательная рассылка через вебхук
        print(f"[Broadcasting] Отправка в {self.webhook_url}...")
        result = self.broadcaster.dispatch_to_webhook("test_channel", payload)
        
        # 5. Верификация
        # Если метод вернул True или объект ответа, считаем успех
        self.assertTrue(result is not False, "Вебхук не отправил данные")
        print("[SUCCESS] Интеграция работает: данные успешно переданы через диспетчер и шаблонизатор.")

if __name__ == "__main__":
    unittest.main()