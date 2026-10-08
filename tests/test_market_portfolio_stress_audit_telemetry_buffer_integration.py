import unittest
import uuid
import random
import os
import time
from skills.market_portfolio_stress_audit_telemetry_buffer import MarketPortfolioStressAuditTelemetryBuffer
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer
from skills.db_storage import DBStorage

class TestMarketPortfolioStressAuditTelemetryBufferIntegration(unittest.TestCase):
    def setUp(self):
        self.db = DBStorage()
        self.visualizer = MarketPortfolioStressAuditVisualizer()
        self.buffer = MarketPortfolioStressAuditTelemetryBuffer(
            storage=self.db,
            visualizer=self.visualizer
        )
        self.test_run_id = str(uuid.uuid4())

    def test_telemetry_buffer_flow_integrity(self):
        # Генерируем пакет случайных данных стресс-аудита
        payload_size = random.randint(5, 15)
        test_data = [
            {
                "audit_id": str(uuid.uuid4()),
                "scenario_id": f"scenario_{random.randint(100, 999)}",
                "stress_impact": random.uniform(-0.5, 0.5),
                "timestamp": time.time()
            }
            for _ in range(payload_size)
        ]

        # Передача данных в буфер
        for entry in test_data:
            self.buffer.push(entry)

        # Инициируем принудительный сброс (flush) в визуализатор
        flush_result = self.buffer.flush()

        # Проверка: визуализатор должен подтвердить получение данных
        self.assertTrue(flush_result, "Буфер не смог передать данные в визуализатор")

        # Проверка целостности в БД (интеграционный аспект)
        for entry in test_data:
            stored_record = self.db.get_record(entry["audit_id"])
            self.assertIsNotNone(stored_record, f"Запись {entry['audit_id']} не найдена в БД")
            self.assertEqual(stored_record["scenario_id"], entry["scenario_id"])

    def test_buffer_overflow_handling(self):
        # Проверка накопления при пиковой нагрузке
        large_payload = [
            {"id": str(uuid.uuid4()), "val": random.random()}
            for _ in range(50)
        ]

        for item in large_payload:
            self.buffer.push(item)

        # Проверка, что буфер не пуст до вызова визуализатора
        self.assertGreater(self.buffer.get_current_queue_size(), 0)

        # Выполняем синхронизацию
        self.buffer.flush()

        # После flush буфер должен быть очищен
        self.assertEqual(self.buffer.get_current_queue_size(), 0)

if __name__ == '__main__':
    unittest.main()