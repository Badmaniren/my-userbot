import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from skills.market_insider_activity_tracker import market_insider_activity_tracker
    from skills.market_anomaly_detector import market_anomaly_detector
    from skills.market_insider_alert_pipeline import market_insider_alert_pipeline
    from skills.market_insider_anomaly_analyzer import market_insider_anomaly_analyzer
    from skills.market_report_generator import market_report_generator
    from skills.market_insider_anomaly_report_bridge import market_insider_anomaly_report_bridge
except ImportError:
    from market_insider_activity_tracker import market_insider_activity_tracker
    from market_anomaly_detector import market_anomaly_detector
    from market_insider_alert_pipeline import market_insider_alert_pipeline
    from market_insider_anomaly_analyzer import market_insider_anomaly_analyzer
    from market_report_generator import market_report_generator
    from market_insider_anomaly_report_bridge import market_insider_anomaly_report_bridge


class TestInsiderAnomalyInvestigationEpic(unittest.TestCase):

    def setUp(self):
        self.test_data_path = "real_market_anomalies_test.json"

        # Создаем реалистичный файл с рыночными данными и инсайдерскими алертами для проверки
        raw_data = [
            {"timestamp": "2023-10-25T10:00:00Z", "ticker": "AAPC", "volume": 1250000, "avg_volume": 150000, "price_change_pct": 5.4, "insider_trades_count": 8, "sec_filing_flag": True},
            {"timestamp": "2023-10-25T10:15:00Z", "ticker": "XYZ", "volume": 50000, "avg_volume": 45000, "price_change_pct": 0.1, "insider_trades_count": 0, "sec_filing_flag": False},
            {"timestamp": "2023-10-25T10:30:00Z", "ticker": "BULL", "volume": 4300000, "avg_volume": 300000, "price_change_pct": 14.2, "insider_trades_count": 15, "sec_filing_flag": True},
            {"timestamp": "2023-10-25T11:00:00Z", "ticker": "TECH", "volume": 800000, "avg_volume": 750000, "price_change_pct": -0.5, "insider_trades_count": 1, "sec_filing_flag": False}
        ]

        with open(self.test_data_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2)

    def tearDown(self):
        if os.path.exists(self.test_data_path):
            os.remove(self.test_data_path)

    def test_insider_anomaly_investigation_pipeline(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ===")
        print("Эпик: Анализ и расследование инсайдерских аномалий рынка")

        # 1. Читаем созданный файл с данными
        with open(self.test_data_path, "r", encoding="utf-8") as f:
            market_records = json.load(f)

        print(f"Загружено записей для анализа из файла: {len(market_records)}")

        # 2. Шаг проверки модулей трекинга и детектирования аномалий
        detected_anomalies = []
        alerted_events = []

        for record in market_records:
            # Имитируем трекинг активности инсайдеров
            activity_score = market_insider_activity_tracker(record)

            # Детектируем рыночную аномалию
            is_anomaly = market_anomaly_detector(record)

            if is_anomaly or activity_score > 0.7:
                detected_anomalies.append({
                    "ticker": record["ticker"],
                    "anomaly": is_anomaly,
                    "activity_score": activity_score
                })

            # Прогон через пайплайн инсайдерских алертов
            alert = market_insider_alert_pipeline(record)
            if alert:
                alerted_events.append(alert)

        print(f"Найденные рыночные аномалии: {detected_anomalies}")
        print(f"Сгенерированные инсайдерские алерты: {len(alerted_events)}")

        # 3. Первый шаг эпика: market_insider_anomaly_analyzer (кросс-валидация)
        analyzed_results = market_insider_anomaly_analyzer(market_records)
        print("Результаты кросс-валидации анализатора аномалий:")
        print(json.dumps(analyzed_results, indent=2, ensure_ascii=False))

        self.assertIsInstance(analyzed_results, (dict, list))
        if isinstance(analyzed_results, dict):
            self.assertIn("status", analyzed_results)

        # 4. Финальный шаг эпика: market_insider_anomaly_report_bridge
        # Соединяет анализатор аномалий с генератором отчетов для автоматического создания расследований
        investigation_report = market_insider_anomaly_report_bridge(analyzed_results, market_report_generator)

        print("Сгенерированный отчет о расследовании инсайдерских аномалий:")
        print(str(investigation_report)[:500] + "..." if len(str(investigation_report)) > 500 else str(investigation_report))

        self.assertIsNotNone(investigation_report)
        print("=== ПРАКТИЧЕСКАЯ ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА ===")


if __name__ == "__main__":
    unittest.main()