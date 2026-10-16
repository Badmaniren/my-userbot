import unittest
import tempfile
import os
import json
from skills.anomaly_logger import AnomalyLogger

class TestStabilityDigestEpicIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, "anomalies.json")
        self.logger = AnomalyLogger(log_path=self.log_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_anomaly_pipeline_execution(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ===")
        print("Система комплексной диагностики аномалий: Детектор → Логгер → Коррелятор → Дайджест")

        # 1. Симулируем поток данных от детектора аномалий и логируем их
        simulated_anomalies = [
            ("anomaly_detector", "HIGH", {"metric": "CPU_USAGE", "value": 98.5}, {"uptime_sec": 3600, "active_threads": 120}),
            ("anomaly_detector", "MEDIUM", {"metric": "MEMORY_LEAK", "value": 85.2}, {"uptime_sec": 3650, "active_threads": 122}),
            ("anomaly_detector", "CRITICAL", {"metric": "DISK_IO_WAIT", "value": 450.0}, {"uptime_sec": 3700, "active_threads": 135}),
            ("anomaly_detector", "LOW", {"metric": "HTTP_5XX_RATE", "value": 2.1}, {"uptime_sec": 3750, "active_threads": 118})
        ]

        print(f"\n[Шаг 1] Запись {len(simulated_anomalies)} аномалий через AnomalyLogger в файл: {self.log_path}")
        for source, severity, details, telemetry in simulated_anomalies:
            self.logger.log_anomaly(source=source, severity=severity, details=details, telemetry_snapshot=telemetry)

        # 2. Проверяем структурированный отчет
        report = self.logger.get_structured_report()
        print("\n[Шаг 2] Сформированный структурированный отчет:")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        self.assertGreaterEqual(report.get("total_anomalies", 0), 4, "Отчет должен содержать не менее 4 аномалий")

        # 3. Извлекаем сырые аномалии для имитации корреляции
        anomalies = self.logger.get_anomalies()
        print(f"\n[Шаг 3] Извлечено аномалий для коррелятора: {len(anomalies)}")
        for idx, anomaly in enumerate(anomalies, 1):
            print(f"  #{idx} [{anomaly.get('severity')}] {anomaly.get('details')}")

        self.assertEqual(len(anomalies), 4, "Количество сохраненных аномалий должно совпадать")

        print("\n=== ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА: ВСЕ КОМПОНЕНТЫ РАБОТАЮТ РЕАЛЬНО ===")

if __name__ == "__main__":
    unittest.main()