import unittest
import uuid
import random
import os
import json
from skills.market_portfolio_stress_audit_telemetry_aggregator import MarketPortfolioStressAuditTelemetryAggregator
from skills.market_portfolio_stress_audit_realtime_streamer import MarketPortfolioStressAuditRealtimeStreamer
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer

class TestMarketPortfolioStressAuditTelemetryAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = MarketPortfolioStressAuditTelemetryAggregator()
        self.streamer = MarketPortfolioStressAuditRealtimeStreamer()
        self.visualizer = MarketPortfolioStressAuditVisualizer()
        self.test_run_id = str(uuid.uuid4())
        self.temp_storage_path = f"test_audit_{self.test_run_id}.json"

    def tearDown(self):
        if os.path.exists(self.temp_storage_path):
            os.remove(self.temp_storage_path)

    def test_stream_to_aggregation_to_visualization_flow(self):
        # Генерируем случайные метрики стресс-теста
        test_payload = {
            "audit_id": self.test_run_id,
            "volatility_index": random.uniform(0.1, 0.9),
            "drawdown_risk": random.uniform(0.01, 0.25),
            "timestamp": random.randint(1600000000, 1700000000)
        }

        # 1. Имитация потока данных через streamer
        stream_data = self.streamer.emit_telemetry(test_payload)
        self.assertIsNotNone(stream_data, "Streamer должен вернуть данные")

        # 2. Агрегация данных (интеграционный вызов)
        # Агрегатор принимает поток и фильтрует его
        aggregated_result = self.aggregator.process_stream(stream_data)

        self.assertEqual(aggregated_result['audit_id'], self.test_run_id)
        self.assertIn('processed_at', aggregated_result)

        # 3. Передача в визуализатор (проверка записи в целевой узел)
        visualization_status = self.visualizer.render_audit_metrics(aggregated_result, output_path=self.temp_storage_path)

        self.assertTrue(visualization_status, "Визуализатор должен подтвердить обработку")
        self.assertTrue(os.path.exists(self.temp_storage_path), "Файл визуализации должен быть создан")

        # 4. Валидация целостности данных в конечном файле
        with open(self.temp_storage_path, 'r') as f:
            stored_data = json.load(f)
            self.assertEqual(stored_data['audit_id'], self.test_run_id)
            self.assertEqual(stored_data['volatility_index'], test_payload['volatility_index'])

if __name__ == '__main__':
    unittest.main()