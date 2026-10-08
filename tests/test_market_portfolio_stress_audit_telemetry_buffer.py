import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
import json
from skills.market_portfolio_stress_audit_telemetry_buffer import StressAuditTelemetryBuffer

class TestStressAuditTelemetryBuffer(unittest.TestCase):

    def setUp(self):
        self.buffer_size = random.randint(10, 100)
        self.buffer = StressAuditTelemetryBuffer(capacity=self.buffer_size)

    def test_buffer_integrity_under_load(self):
        """Проверка целостности данных при накоплении и сбросе."""
        test_data = {
            "audit_id": uuid.uuid4().hex,
            "payload": "".join(random.choices(string.ascii_letters, k=20)),
            "timestamp": random.random()
        }

        self.buffer.push(test_data)
        self.assertEqual(len(self.buffer), 1)

        extracted = self.buffer.flush()
        self.assertEqual(extracted[0]["audit_id"], test_data["audit_id"])
        self.assertEqual(len(self.buffer), 0)

    def test_overflow_handling(self):
        """Проверка поведения при переполнении буфера."""
        capacity = random.randint(5, 10)
        buffer = StressAuditTelemetryBuffer(capacity=capacity)

        for _ in range(capacity + 5):
            buffer.push({"id": uuid.uuid4().hex})

        self.assertEqual(len(buffer), capacity)

    def test_telemetry_stream_persistence(self):
        """Имитация передачи данных в визуализатор через мок-поток."""
        mock_visualizer = MagicMock()
        random_stream_id = uuid.uuid4().hex

        with patch('skills.market_portfolio_stress_audit_telemetry_buffer.market_portfolio_stress_audit_visualizer', mock_visualizer):
            data = {"stream_id": random_stream_id, "val": random.uniform(0, 1000)}
            self.buffer.push(data)
            self.buffer.transmit(mock_visualizer)

            mock_visualizer.receive.assert_called_with(data)

    def test_data_corruption_resistance(self):
        """Проверка обработки некорректных типов данных."""
        garbage_data = b'\x00\xff\xde\xad\xbe\xef'
        with self.assertRaises(ValueError):
            self.buffer.push(garbage_data)

    def test_buffer_serialization_integrity(self):
        """Проверка сериализации буфера в байтовый поток."""
        random_key = uuid.uuid4().hex
        random_val = random.randint(1, 9999)
        self.buffer.push({random_key: random_val})

        serialized = self.buffer.serialize()
        self.assertIsInstance(serialized, bytes)

        deserialized = json.loads(serialized.decode('utf-8'))
        self.assertEqual(deserialized[0][random_key], random_val)

    def test_flush_to_storage_mock(self):
        """Проверка записи в хранилище через мок-интерфейс."""
        mock_storage = MagicMock()
        random_audit_tag = uuid.uuid4().hex

        with patch('skills.market_portfolio_stress_audit_telemetry_buffer.db_storage', mock_storage):
            self.buffer.push({"tag": random_audit_tag})
            self.buffer.persist_to_storage()

            args, _ = mock_storage.save.call_args
            self.assertEqual(args[0][0]["tag"], random_audit_tag)

    def test_stress_threshold_trigger(self):
        """Проверка срабатывания триггера при достижении критического объема."""
        threshold = random.randint(2, 5)
        buffer = StressAuditTelemetryBuffer(capacity=10, threshold=threshold)

        with patch('skills.market_portfolio_stress_audit_telemetry_buffer.market_portfolio_stress_audit_scheduler_hub') as mock_hub:
            for i in range(threshold):
                buffer.push({"seq": i})

            self.assertTrue(mock_hub.notify_overflow.called)

if __name__ == '__main__':
    unittest.main()