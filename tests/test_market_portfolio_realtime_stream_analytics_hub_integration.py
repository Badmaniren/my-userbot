import unittest
import os
import uuid
import tempfile
from skills.market_portfolio_realtime_stream_analytics_hub import (
    MarketPortfolioRealtimeStreamAnalyticsHub,
    process_realtime_stream_hub
)

class TestMarketPortfolioRealtimeStreamAnalyticsHubIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"storage_{uuid.uuid4()}.json")
        self.output_path = os.path.join(self.temp_dir.name, f"output_{uuid.uuid4()}.json")
        self.stream_source = f"stream_src_{uuid.uuid4()}"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        
        # Создаем пустой файл хранилища для корректной инициализации аналитики
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{}")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_integration_hub_flow(self):
        # Генерируем случайный контекст для потока
        context_key = str(uuid.uuid4())
        context_val = str(uuid.uuid4())
        context = {context_key: context_val}

        hub = MarketPortfolioRealtimeStreamAnalyticsHub(self.storage_file, self.stream_source)

        # Тест метода process_stream
        stream_result = hub.process_stream(context)
        self.assertIsInstance(stream_result, dict)

        # Тест метода audit_stream_data
        payload = {str(uuid.uuid4()): str(uuid.uuid4())}
        audit_result = hub.audit_stream_data(payload, self.output_path)
        self.assertIsInstance(audit_result, dict)

        # Тест получения метрик реального времени
        metrics_result = hub.get_realtime_metrics(self.symbol)
        self.assertIsInstance(metrics_result, dict)

        # Тест оценки производительности потока
        performance_result = hub.evaluate_stream_performance(self.symbol)
        self.assertIsInstance(performance_result, dict)

        # Тест внешней функции process_realtime_stream_hub
        global_process_result = process_realtime_stream_hub(
            output_path=self.output_path,
            storage_file=self.storage_file,
            symbol=self.symbol
        )
        
        self.assertIsInstance(global_process_result, dict)
        self.assertEqual(global_process_result.get("output_path"), self.output_path)
        self.assertEqual(global_process_result.get("storage_file"), self.storage_file)
        self.assertIn("metrics", global_process_result)
        self.assertEqual(global_process_result["metrics"].get("symbol"), self.symbol)

if __name__ == "__main__":
    unittest.main()