import unittest
import urllib.request
import xml.etree.ElementTree as ET
import time

from skills.incident_severity_evaluator import incident_severity_evaluator
from skills.incident_notification_bridge import incident_notification_bridge
from skills.incident_notification_broadcaster import incident_notification_broadcaster
from skills.notification_channel_dispatcher import notification_channel_dispatcher

class TestIncidentNotificationPipelineRealWorld(unittest.TestCase):

    def test_end_to_end_real_world_incident_broadcast(self):
        rss_url = "https://news.ycombinator.com/rss"
        xml_data = None

        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    rss_url,
                    headers={'User-Agent': 'UngiIncidentChecker/1.0'}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    xml_data = response.read()
                break
            except Exception as e:
                if attempt == 1:
                    self.fail(f"Сетевой запрос к {rss_url} не удался после 2 попыток: {e}")
                time.sleep(1)

        self.assertIsNotNone(xml_data, "Данные RSS не должны быть пустыми")

        root = ET.fromstring(xml_data)
        item = root.find('./channel/item')
        self.assertIsNotNone(item, "В RSS-ленте Hacker News должны быть элементы")

        title = item.find('title').text
        link = item.find('link').text

        print("\n[РЕАЛЬНЫЙ МИР] Успешно получена живая новость из Hacker News RSS:")
        print(f" -> Заголовок: {title}")
        print(f" -> Ссылка: {link}")

        raw_incident = {
            "source": "Hacker News RSS",
            "title": title,
            "link": link,
            "description": f"Обнаружено внешнее упоминание в фиде: {title}"
        }

        evaluator = incident_severity_evaluator()
        classified_incident = evaluator.evaluate(raw_incident)
        self.assertIn("severity", classified_incident)
        print(f" [1/3 Обнаружение & Классификация] Инцидент классифицирован как: {classified_incident.get('severity')}")

        bridge = incident_notification_bridge()
        bridged_payload = bridge.transform(classified_incident)
        self.assertIsNotNone(bridged_payload)
        print(" [2/3 Мост уведомлений] Данные успешно преобразованы через incident_notification_bridge.")

        dispatcher = notification_channel_dispatcher()
        broadcaster = incident_notification_broadcaster(dispatcher=dispatcher)
        broadcast_result = broadcaster.broadcast(bridged_payload)

        self.assertTrue(broadcast_result, "Широковещательная рассылка должна завершиться успехом")
        print(" [3/3 Широковещательная рассылка] Уведомление успешно разослано по каналам без антипаттернов.")
        print("[ОТЧЕТ] Проверка завершенного эпика прошла успешно на реальных данных из сети!\n")

if __name__ == "__main__":
    unittest.main()