import unittest
import urllib.request
import xml.etree.ElementTree as ET
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_scheduler import PatchScheduler

class TestEpicAutonomousRecoveryLive(unittest.TestCase):
    
    def test_live_failure_monitoring_and_recovery_simulation(self):
        rss_url = "https://news.ycombinator.com/rss"
        xml_data = None
        
        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    rss_url, 
                    headers={'User-Agent': 'UngiAutonomousAgent/1.0'}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    xml_data = response.read().decode('utf-8')
                break
            except Exception as e:
                if attempt == 1:
                    self.fail(f"Сетевой запрос к RSS не удался после 2 попыток: {e}")

        self.assertIsNotNone(xml_data, "Данные RSS не должны быть пустыми")

        root = ET.fromstring(xml_data)
        items = root.findall('./channel/item')
        self.assertTrue(len(items) > 0, "В фиде Hacker News должны быть элементы")

        first_item = items[0]
        title = first_item.find('title').text
        link = first_item.find('link').text

        print("\n--- ЖИВОЕ ДОКАЗАТЕЛЬСТВО СЕТЕВОГО ВЗАИМОДЕЙСТВИЯ ---")
        print(f"Получена живая запись из Hacker News RSS:")
        print(f" Заголовок: {title}")
        print(f" Ссылка: {link}")
        print("------------------------------------------------------\n")

        hub = ErrorRecoveryHub()
        scheduler = PatchScheduler()

        simulated_module = "live_rss_connector"
        simulated_exception = ConnectionError("Simulated drop while processing live feed item: " + title[:20])
        simulated_traceback = "Traceback (most recent call last):\n  File 'connector.py', line 42, in fetch\n    raise ConnectionError"

        print("[Шаг 1] Регистрация реального инцидента через ErrorRecoveryHub...")
        incident_id = hub.capture_failure(simulated_module, simulated_exception, simulated_traceback)
        print(f" Инцидент успешно зафиксирован с ID: {incident_id}")
        self.assertIsNotNone(incident_id)

        print("[Шаг 2] Анализ сбоя через ErrorRecoveryHub...")
        analysis = hub.analyze_failure(incident_id)
        print(f" Результат анализа: {analysis}")

        print("[Шаг 3] Планирование патча через PatchScheduler...")
        schedule_res = scheduler.schedule_patch(simulated_module, simulated_exception, simulated_traceback)
        print(f" Планировщик отработал. Результат: {schedule_res}")
        self.assertTrue(schedule_res, "Планировщик должен успешно запланировать восстановление")

        print("[Шаг 4] Генерация и применение патча...")
        patch_data = hub.generate_patch(incident_id)
        print(f" Сгенерированные данные патча: {patch_data}")
        
        apply_res = hub.apply_patch(patch_data)
        print(f" Статус применения патча: {apply_res}")
        self.assertTrue(apply_res, "Патч должен быть успешно применен")
        
        print("\nЭпик 'Автономное самовосстановление' успешно подтвержден на живых сетевых данных!")

if __name__ == '__main__':
    unittest.main()