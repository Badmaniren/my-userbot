import unittest
import time
import urllib.request
import xml.etree.ElementTree as ET

from skills.incident_aggregator import IncidentAggregator
from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class TestIncidentResponseAndEscalationEpicRealWorld(unittest.TestCase):

    def test_real_world_incident_auto_escalation_and_recovery_cycle(self):
        print("\n[REAL-WORLD DEMO] Starting live test for: Автоматизированное реагирование и эскалация критических инцидентов")

        rss_url = "https://news.ycombinator.com/rss"
        xml_data = None
        retries = 2

        for attempt in range(retries):
            try:
                print(f"[NETWORK] Fetching live RSS feed from Hacker News (Attempt {attempt + 1}/{retries})...")
                req = urllib.request.Request(
                    rss_url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    xml_data = response.read()
                break
            except Exception as e:
                print(f"[NETWORK WARNING] Attempt {attempt + 1} failed: {e}")
                if attempt == retries - 1:
                    self.fail("Failed to fetch live RSS feed after 2 attempts.")
                time.sleep(1)

        self.assertIsNotNone(xml_data)

        root = ET.fromstring(xml_data)
        items = root.findall('./channel/item')
        self.assertTrue(len(items) > 0, "RSS feed must contain items")

        first_item = items[0]
        title = first_item.find('title').text if first_item.find('title') is not None else "No Title"
        link = first_item.find('link').text if first_item.find('link') is not None else "No Link"

        print(f"[LIVE DATA CAPTURED] Headline: '{title}'")
        print(f"[LIVE DATA CAPTURED] Link: '{link}'")

        raw_incident = {
            "source": "HackerNews_RSS",
            "title": title,
            "url": link,
            "timestamp": time.time(),
            "raw_payload": f"Live external alert parsed from HN: {title}"
        }

        aggregator = IncidentAggregator()
        aggregated_incident = aggregator.aggregate(raw_incident)
        print(f"[MODULE: incident_aggregator] Aggregated ID: {aggregated_incident.get('id', 'N/A')}")

        evaluator = IncidentSeverityEvaluator()
        severity_result = evaluator.evaluate(aggregated_incident)
        print(f"[MODULE: incident_severity_evaluator] Evaluated Severity: {severity_result}")

        escalation_engine = IncidentAutoEscalationEngine()
        escalation_result = escalation_engine.process(aggregated_incident, severity_result)
        print(f"[MODULE: incident_auto_escalation_engine] Escalation Status: {escalation_result}")

        recovery_dispatcher = IncidentAutoRecoveryDispatcher()
        dispatch_result = recovery_dispatcher.dispatch(aggregated_incident, escalation_result)
        print(f"[MODULE: incident_auto_recovery_dispatcher] Recovery Dispatch Status: {dispatch_result}")

        self.assertIsNotNone(aggregated_incident)
        self.assertIsNotNone(severity_result)
        self.assertIsNotNone(escalation_result)
        self.assertIsNotNone(dispatch_result)

        print("[SUCCESS] Real-world incident auto-escalation and recovery cycle executed successfully with live data.")


if __name__ == '__main__':
    unittest.main()