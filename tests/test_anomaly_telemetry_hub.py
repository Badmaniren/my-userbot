import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import os

from skills.anomaly_telemetry_hub import start_new

class TestAnomalyTelemetryHub(unittest.TestCase):

    def setUp(self):
        self.random_prefix = uuid.uuid4().hex
        self.random_data_key = f"key_{self.random_prefix}"
        self.random_data_value = random.randint(1000, 99999)
        self.payload = {
            self.random_data_key: self.random_data_value,
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "source": f"module_{uuid.uuid4().hex[:6]}"
        }

    def test_start_new_filters_valid_data(self):
        """Архитектор требует: проверка фильтрации телеметрии с динамическими непредсказуемыми данными."""
        noise_key = f"noise_{uuid.uuid4().hex}"
        noise_val = f"garbage_{uuid.uuid4().hex}"

        input_structure = [
            self.payload,
            {noise_key: noise_val}
        ]

        result = start_new(input_structure)

        self.assertIsInstance(result, (list, dict), "Функция должна возвращать структурированный результат")

        if isinstance(result, list):
            found = False
            for item in result:
                if isinstance(item, dict) and self.random_data_key in item:
                    self.assertEqual(item[self.random_data_key], self.random_data_value)
                    found = True
            self.assertTrue(found, "Фильтр потерял валидные данные телеметрии")
        elif isinstance(result, dict):
            self.assertIn(self.random_data_key, result)
            self.assertEqual(result[self.random_data_key], self.random_data_value)

    def test_start_new_with_io_stream_chaos(self):
        """Инспекция потоков телеметрии: передача рандомного потока байтов вместо словаря."""
        random_bytes = f"TELEMETRY_STREAM_{uuid.uuid4().hex}:{random.random()}".encode('utf-8')
        stream_mock = io.BytesIO(random_bytes)

        with patch('skills.anomaly_telemetry_hub.open', return_value=stream_mock, create=True) as mock_open:
            try:
                res = start_new(stream_mock)
                self.assertIsNotNone(res)
            except Exception as e:
                self.assertIsInstance(e, (TypeError, ValueError, AttributeError),
                                      f"Неожиданный тип исключения при обработке потока: {type(e)}")

    def test_start_new_empty_and_edge_cases(self):
        """Стресс-тест на аномально пустые или мусорные входные данные."""
        empty_payloads = [
            [],
            {},
            "",
            None,
            random.randint(-100000, -1)
        ]

        for p in empty_payloads:
            try:
                res = start_new(p)
                self.assertIsNotNone(res, "Функция не должна возвращать None даже при получении мусора")
            except Exception as e:
                self.assertIsInstance(e, (TypeError, ValueError, KeyError),
                                      f"Исключение должно быть предсказуемым, получено: {type(e)}")

if __name__ == '__main__':
    unittest.main()