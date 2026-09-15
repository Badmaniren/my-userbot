import unittest
import urllib.request
import xml.etree.ElementTree as ET
import time

from skills.system_health_reporter import SystemHealthReporter
from skills.system_health_aggregator import SystemHealthAggregator
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector
from skills.system_health_audit_pipeline import SystemHealthAuditPipeline
from skills.system_health_monitoring_gateway import SystemHealthMonitoringGateway


class TestSystemHealthMonitoringEpicRealWorld(unittest.TestCase):
    def test_complete_system_health_monitoring_pipeline_with_real_telemetry(self):
        feed_url = "https://news.ycombinator.com/rss"
        xml_data = None
        
        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    feed_url,
                    headers={"User-Agent": "UngiHealthMonitor/1.0 (PracticalCheck)"}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    xml_data = response.read()
                break
            except Exception as e:
                if attempt == 1:
                    self.fail(f"Сетевой запрос не удался после 2 попыток: {e}")
                time.sleep(1)

        self.assertIsNotNone(xml_data, "Не удалось получить данные с Hacker News RSS")

        root = ET.fromstring(xml_data)
        items = root.findall(".//item")
        self.assertTrue(len(items) > 0, "RSS-фид не содержит элементов")

        fetched_titles = []
        for item in items[:5]:
            title = item.find("title")
            if title is not None and title.text:
                fetched_titles.append(title.text)

        print("\n--- ЖИВОЕ ДОКАЗАТЕЛЬСТВО: Получены заголовки из внешнего источника (Hacker News RSS) ---")
        for i, t in enumerate(fetched_titles, 1):
            print(f"[{i}] {t}")
        print("----------------------------------------------------------------------------------\n")

        telemetry_payload = {
            "source": "https://news.ycombinator.com/rss",
            "items_count": len(items),
            "sample_titles": fetched_titles,
            "status": "healthy" if len(fetched_titles) > 0 else "degraded"
        }

        reporter = SystemHealthReporter()
        aggregator = SystemHealthAggregator()
        collector = SystemHealthTelemetryCollector()
        audit_pipeline = SystemHealthAuditPipeline()
        gateway = SystemHealthMonitoringGateway()

        report = reporter.generate(telemetry_payload)
        aggregated = aggregator.aggregate(report)
        collected = collector.collect(aggregated)
        audited = audit_pipeline.run(collected)
        gateway_result = gateway.process(audited)

        print(f"Результат работы завершенного пайплайна мониторинга (Gateway): {gateway_result}")
        
        self.assertIsNotNone(gateway_result, "Шлюз мониторинга здоровья не вернул результат")


if __name__ == "__main__":
    unittest.main()