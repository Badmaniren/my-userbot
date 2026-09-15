import unittest
import urllib.request
import xml.etree.ElementTree as ET

from skills.system_health_reporter import SystemHealthReporter
from skills.system_health_aggregator import SystemHealthAggregator
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector
from skills.system_health_audit_pipeline import SystemHealthAuditPipeline
from skills.system_health_monitoring_gateway import SystemHealthMonitoringGateway


class TestSystemHealthMonitoringEpicLive(unittest.TestCase):

    def test_live_system_health_monitoring_pipeline(self):
        rss_url = "https://news.ycombinator.com/rss"
        xml_data = None
        
        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    rss_url, 
                    headers={'User-Agent': 'UngiHealthMonitor/1.0'}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    xml_data = response.read()
                break
            except Exception as e:
                if attempt == 1:
                    self.fail(f"Сетевой запрос к RSS не удался после 2 попыток: {e}")

        self.assertIsNotNone(xml_data, "Данные телеметрии не были получены.")

        root = ET.fromstring(xml_data)
        items = root.findall('./channel/item')
        self.assertGreater(len(items), 0, "Фид не содержит элементов.")

        telemetry_feed = []
        print("\n--- ЖИВЫЕ ДАННЫЕ ТЕЛЕМЕТРИИ (Hacker News RSS) ---")
        for item in items[:3]:
            title = item.find('title').text if item.find('title') is not None else "No Title"
            link = item.find('link').text if item.find('link') is not None else "No Link"
            telemetry_feed.append({"title": title, "link": link})
            print(f"• Заголовок: {title}")
            print(f"  Ссылка: {link}")
        print("--------------------------------------------------\n")

        reporter = SystemHealthReporter()
        aggregator = SystemHealthAggregator()
        collector = SystemHealthTelemetryCollector()
        pipeline = SystemHealthAuditPipeline()
        gateway = SystemHealthMonitoringGateway()

        report = reporter.generate(telemetry_feed)
        aggregated = aggregator.aggregate(report)
        collected = collector.collect(aggregated)
        audited = pipeline.run(collected)
        summary = gateway.export(audited)

        print("--- РЕЗУЛЬТАТ ЭКСПОРТА СВОДКИ МОНИТОРИНГА ---")
        print(summary)
        print("---------------------------------------------")

        self.assertIsNotNone(summary, "Шлюз мониторинга не смог экспортировать сводку.")


if __name__ == '__main__':
    unittest.main()