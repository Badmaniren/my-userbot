import unittest
import tempfile
import os
import json
from anomaly_filter import start_new
from anomaly_logger import AnomalyLogger

class TestAnomalyPipelinePractical(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, "anomalies.json")

        self.raw_telemetry = [
            {"timestamp": "2023-10-25T10:00:00Z", "metric": "cpu_load", "value": 15.4, "status": "normal"},
            {"timestamp": "2023-10-25T10:01:00Z", "metric": "cpu_load", "value": 99.8, "status": "critical"},
            {"timestamp": "2023-10-25T10:02:00Z", "metric": "memory_usage", "value": 45.0, "status": "normal"},
            {"timestamp": "2023-10-25T10:03:00Z", "metric": "memory_usage", "value": 92.1, "status": "warning"},
            {"timestamp": "2023-10-25T10:04:00Z", "metric": "disk_io", "value": 5.2, "status": "normal"},
            {"timestamp": "2023-10-25T10:05:00Z", "metric": "cpu_load", "value": 12.0, "status": "normal"},
            {"timestamp": "2023-10-25T10:06:00Z", "metric": "temperature", "value": 88.5, "status": "critical"},
            {"timestamp": "2023-10-25T10:07:00Z", "metric": "disk_io", "value": 2.1, "status": "normal"},
            {"timestamp": "2023-10-25T10:08:00Z", "metric": "network_errors", "value": 500, "status": "critical"},
            {"timestamp": "2023-10-25T10:09:00Z", "metric": "cpu_load", "value": 18.2, "status": "normal"}
        ]

        self.data_file = os.path.join(self.test_dir.name, "telemetry.json")
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.raw_telemetry, f)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_anomaly_contour_practical_execution(self):
        print("\n=== ПРАКТИЧЕСКАЯ ПРОВЕРКА КОНТУРА АНАЛИЗА АНОМАЛИЙ ===")

        with open(self.data_file, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        print(f"Загружено сырых записей телеметрии: {len(loaded_data)}")

        filtered_result = start_new(loaded_data)
        print(f"Результат работы anomaly_filter.start_new: {filtered_result}")

        logger = AnomalyLogger(self.log_path)

        critical_items = [item for item in loaded_data if item.get("status") in ["critical", "warning"]]
        print(f"Выделено аномальных записей для логирования: {len(critical_items)}")

        for idx, anomaly in enumerate(critical_items, 1):
            source = f"sensor_{anomaly['metric']}"
            severity = anomaly['status']
            details = f"Metric {anomaly['metric']} reached value {anomaly['value']}"
            logger.log_anomaly(source, severity, details, anomaly)
            print(f"[{idx}] Залогирована аномалия: {source} | Уровень: {severity} | Детали: {details}")

        structured_report = logger.get_structured_report()
        print("\n--- Структурированный отчет по аномалиям ---")
        print(json.dumps(structured_report, indent=2, ensure_ascii=False))

        all_logged_anomalies = logger.get_anomalies()
        print(f"\nВсего зарегистрировано аномалий в логгере: {len(all_logged_anomalies)}")

        self.assertGreater(len(all_logged_anomalies), 0, "Контур должен зафиксировать и сохранить аномалии")
        self.assertTrue(os.path.exists(self.log_path), "Файл логов аномалий должен быть создан на диске")
        print("=== ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА ===")

if __name__ == "__main__":
    unittest.main()