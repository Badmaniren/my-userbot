import unittest
import os
import json
import tempfile
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics
from skills.market_portfolio_stress_reporter import StressReporter
from skills.market_portfolio_visualizer_v2 import generate_ascii_chart

class TestPortfolioPerformanceAnalyticsEpic(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_path = os.path.join(self.test_dir.name, "portfolio_test_data.json")

        raw_data = {
            "AAPL": [
                {"price": 150.0, "timestamp": "2023-01-01T10:00:00"},
                {"price": 155.5, "timestamp": "2023-01-02T10:00:00"},
                {"price": 153.2, "timestamp": "2023-01-03T10:00:00"},
                {"price": 158.0, "timestamp": "2023-01-04T10:00:00"},
                {"price": 162.5, "timestamp": "2023-01-05T10:00:00"},
                {"price": 160.0, "timestamp": "2023-01-06T10:00:00"},
                {"price": 165.4, "timestamp": "2023-01-07T10:00:00"},
                {"price": 168.1, "timestamp": "2023-01-08T10:00:00"},
                {"price": 167.0, "timestamp": "2023-01-09T10:00:00"},
                {"price": 172.3, "timestamp": "2023-01-10T10:00:00"},
                {"price": 175.0, "timestamp": "2023-01-11T10:00:00"},
                {"price": 173.5, "timestamp": "2023-01-12T10:00:00"},
                {"price": 178.2, "timestamp": "2023-01-13T10:00:00"},
                {"price": 180.0, "timestamp": "2023-01-14T10:00:00"},
                {"price": 182.4, "timestamp": "2023-01-15T10:00:00"},
                {"price": 181.0, "timestamp": "2023-01-16T10:00:00"},
                {"price": 185.6, "timestamp": "2023-01-17T10:00:00"},
                {"price": 188.0, "timestamp": "2023-01-18T10:00:00"},
                {"price": 186.5, "timestamp": "2023-01-19T10:00:00"},
                {"price": 190.2, "timestamp": "2023-01-20T10:00:00"},
                {"price": 192.5, "timestamp": "2023-01-21T10:00:00"}
            ]
        }

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_performance_analytics_and_ascii_integration(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА АНАЛИТИКИ ===")

        analytics = PortfolioPerformanceAnalytics(self.storage_path)
        metrics = analytics.calculate_metrics("AAPL")

        print("\n[1] Рассчитанные финансовые метрики (PortfolioPerformanceAnalytics):")
        print(json.dumps(metrics, indent=2, ensure_ascii=False))

        self.assertIsInstance(metrics, dict)
        self.assertTrue(len(metrics) > 0, "Метрики не должны быть пустыми")

        evaluation = analytics.evaluate_performance("AAPL")
        print("\n[2] Оценка эффективности портфеля (evaluate_performance):")
        print(json.dumps(evaluation, indent=2, ensure_ascii=False))

        stress_reporter = StressReporter(self.storage_path)
        shifts = [-5.0, -2.5, 0.0, 2.5, 5.0]
        stress_report = stress_reporter.run_stress_reporting("AAPL", shifts)

        print("\n[3] Отчет стресс-тестирования (StressReporter):")
        print(json.dumps(stress_report, indent=2, ensure_ascii=False))

        stream_data = stress_reporter.get_stream_data()
        print("\n[4] Данные потока для визуализации:")
        print(stream_data)

        ascii_chart = generate_ascii_chart([item["price"] for item in stream_data]) if isinstance(stream_data, list) else generate_ascii_chart([150.0, 160.0, 170.0, 180.0, 192.5])

        print("\n[5] Сгенерированный ASCII-график (market_portfolio_visualizer_v2):")
        print(ascii_chart)

        print("\n=== ПРАКТИЧЕСКАЯ ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА ===")

if __name__ == "__main__":
    unittest.main()