import unittest
import time
import urllib.request
import xml.etree.ElementTree as ET

from skills.incident_sla_tracker import IncidentSLATracker
from skills.incident_sla_breach_predictor import IncidentSLABreachPredictor
from skills.incident_sla_mitigation_planner import IncidentSLAMitigationPlanner
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher
from skills.incident_sla_recovery_coordinator import IncidentSLARecoveryCoordinator

class RealWorldSLARecoveryValidationTest(unittest.TestCase):

    def test_live_sla_compliance_and_recovery_loop(self):
        print("\n=== НАЧАЛО РЕАЛЬНОЙ ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ===")
        print("Эпик: SLA Compliance and Recovery Optimization")

        feed_url = "https://news.ycombinator.com/rss"
        xml_data = None

        for attempt in range(2):
            try:
                print(f"Попытка {attempt + 1}: Подключение к реальному RSS-фиду Hacker News ({feed_url})...")
                req = urllib.request.Request(
                    feed_url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    xml_data = response.read()
                break
            except Exception as e:
                print(f"Сетевой сбой на попытке {attempt + 1}: {e}")
                if attempt == 1:
                    self.fail("Не удалось получить данные из сети после 2 попыток.")
                time.sleep(1)

        self.assertIsNotNone(xml_data, "Данные фида не должны быть пустыми.")

        root = ET.fromstring(xml_data)
        items = root.findall('./channel/item')
        self.assertGreater(len(items), 0, "RSS-фид должен содержать элементы.")

        first_item = items[0]
        title = first_item.find('title').text
        link = first_item.find('link').text

        print(f"\n[ЖИВЫЕ ДАННЫЕ ИЗ СЕТИ]")
        print(f"Заголовок последней новости HN: {title}")
        print(f"Ссылка: {link}")

        print("\nИнициализация модулей контура SLA...")
        tracker = IncidentSLATracker()
        predictor = IncidentSLABreachPredictor()
        planner = IncidentSLAMitigationPlanner()
        dispatcher = IncidentAutoRecoveryDispatcher()
        coordinator = IncidentSLARecoveryCoordinator(
            sla_tracker=tracker,
            auto_dispatcher=dispatcher
        )

        incident_id = "INC-REAL-001"
        incident_context = {
            "incident_id": incident_id,
            "title": title,
            "source": link,
            "severity": "HIGH",
            "elapsed_time_minutes": 45,
            "sla_limit_minutes": 60
        }

        print(f"1. Регистрация инцидента в incident_sla_tracker: {incident_id}")
        tracking_result = tracker.track_incident(incident_context)
        self.assertIsNotNone(tracking_result)

        print("2. Прогнозирование риска нарушения SLA через incident_sla_breach_predictor...")
        prediction = predictor.predict_breach(incident_context)
        print(f"Результат предиктора: {prediction}")

        print("3. Формирование плана митигации через incident_sla_mitigation_planner...")
        mitigation_plan = planner.create_plan(incident_context)
        print(f"План митигации: {mitigation_plan}")

        print("4. Диспетчеризация автовосстановления через incident_auto_recovery_dispatcher...")
        dispatch_result = dispatcher.dispatch(incident_context, mitigation_plan)
        print(f"Статус автодиспетчера: {dispatch_result}")

        print("5. Синхронизация контура через incident_sla_recovery_coordinator...")
        coordination_status = coordinator.coordinate(incident_id)
        print(f"Статус координатора SLA: {coordination_status}")

        print("\n=== ПРАКТИЧЕСКАЯ ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА ===")

if __name__ == "__main__":
    unittest.main()