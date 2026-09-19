import unittest
import time
import urllib.request
import xml.etree.ElementTree as ET

from skills.telemetry_streamer import telemetry_streamer
from skills.telemetry_processor import telemetry_processor
from skills.system_health_telemetry_collector import system_health_telemetry_collector

class RealtimeTelemetryPipelineVerification(unittest.TestCase):
    def test_live_telemetry_pipeline_end_to_end(self):
        rss_url = "https://news.ycombinator.com/rss"
        raw_feed_data = None

        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    rss_url,
                    headers={"User-Agent": "UngiTelemetryVerification/1.0"}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    raw_feed_data = response.read()
                break
            except Exception as e:
                if attempt == 1:
                    self.fail(f"Сетевой сбой при доступе к реальному источнику телеметрии после 2 попыток: {e}")
                time.sleep(1)

        self.assertIsNotNone(raw_feed_data, "Не удалось получить данные из публичного фида.")

        try:
            root = ET.fromstring(raw_feed_data)
            items = root.findall(".//item")
            self.assertGreater(len(items), 0, "В полученном RSS-фиде отсутствуют элементы.")

            sample_item = items[0]
            title = sample_item.find("title").text if sample_item.find("title") is not None else "No Title"
            link = sample_item.find("link").text if sample_item.find("link") is not None else "No Link"

            raw_payload = {
                "source": "HackerNews_RSS",
                "telemetry_title": title,
                "telemetry_target": link,
                "timestamp": time.time()
            }
        except Exception as e:
            self.fail(f"Ошибка парсинга живого XML-потока: {e}")

        print(f"\n[LIVE STREAMER] Получены реальные сырые данные: Title='{title}', Link='{link}'")

        streamer_result = telemetry_streamer(raw_payload)
        self.assertIsNotNone(streamer_result, "telemetry_streamer вернул None")

        processed_data = telemetry_processor(streamer_result)
        self.assertIsNotNone(processed_data, "telemetry_processor вернул None")
        print(f"[PROCESSOR] Данные успешно очищены и отформатированы: {processed_data}")

        collector_result = system_health_telemetry_collector(processed_data)
        self.assertIsNotNone(collector_result, "system_health_telemetry_collector вернул None")
        print(f"[HEALTH COLLECTOR] Телеметрия успешно обработана системой без мок-заглушек: {collector_result}")

        self.assertTrue(
            isinstance(collector_result, (dict, str)),
            "Результат коллектора должен быть структурированным."
        )

if __name__ == "__main__":
    unittest.main()