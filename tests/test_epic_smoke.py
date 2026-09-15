import unittest
import urllib.request
import xml.etree.ElementTree as ET
import time

from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.notification_template_engine import NotificationTemplateEngine
from skills.notification_webhook_broadcaster import NotificationWebhookBroadcaster

class TestEpicNotificationSystemLive(unittest.TestCase):

    def test_live_rss_digest_and_broadcast(self):
        rss_url = "https://news.ycombinator.com/rss"
        feed_data = None

        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    rss_url,
                    headers={'User-Agent': 'UngiPracticalTestAgent/1.0'}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    feed_data = response.read()
                break
            except Exception as e:
                if attempt == 1:
                    self.fail(f"Сетевой запрос к RSS не удался после 2 попыток: {e}")
                time.sleep(1)

        self.assertIsNotNone(feed_data, "Не удалось получить данные из сети")

        root = ET.fromstring(feed_data)
        items = root.findall('.//item')
        self.assertTrue(len(items) > 0, "В RSS-фиде отсутствуют элементы")

        first_item = items[0]
        title = first_item.find('title').text if first_item.find('title') is not None else "Без заголовка"
        link = first_item.find('link').text if first_item.find('link') is not None else "Без ссылки"

        print(f"\n[LIVE PROOF] Получен реальный заголовок из HN RSS: {title}")
        print(f"[LIVE PROOF] Ссылка на материал: {link}")

        dispatcher = NotificationChannelDispatcher()
        template_engine = NotificationTemplateEngine()
        broadcaster = NotificationWebhookBroadcaster()

        dispatcher.register_channel("live_console", {"type": "stdout", "active": True})
        broadcaster.register_webhook_channel("live_webhook", {"url": "https://httpbin.org/post", "active": True})

        raw_incident_data = {
            "source": "Hacker News RSS Feed",
            "article_title": title,
            "article_link": link,
            "status": "digest_processed"
        }

        notification_payload = template_engine.generate_notification_payload(
            severity="INFO",
            incident_id="INC-LIVE-001",
            raw_data=raw_incident_data
        )

        self.assertIn("incident_id", notification_payload)
        self.assertEqual(notification_payload["incident_id"], "INC-LIVE-001")
        print(f"[TEMPLATE ENGINE] Сгенерированный полезный груз: {notification_payload}")

        dispatch_success = dispatcher.dispatch("live_console", notification_payload)
        self.assertTrue(dispatch_success, "Диспетчер не смог отправить уведомление в канал")

        broadcast_result = broadcaster.broadcast_incident(
            severity="INFO",
            incident_id="INC-LIVE-001",
            raw_data=raw_incident_data,
            template_name="default"
        )

        print(f"[BROADCASTER] Результат широкого вещания: {broadcast_result}")
        self.assertIsNotNone(broadcast_result)

if __name__ == '__main__':
    unittest.main()