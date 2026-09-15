import unittest
from unittest.mock import patch
import random
import uuid
import time
from collections import deque

# Импортируем тестируемый класс
from skills.system_health_tracker import SystemHealthTracker

class TestSystemHealthTracker(unittest.TestCase):
    def setUp(self):
        self.max_records = random.randint(50, 150)
        self.tracker = SystemHealthTracker(max_records=self.max_records)

    def test_initialization(self):
        self.assertEqual(self.tracker.max_records, self.max_records)
        self.assertEqual(len(self.tracker.metrics), 0)
        self.assertEqual(len(self.tracker.errors), 0)

    def test_record_execution_time(self):
        op_name = f"op_{uuid.uuid4().hex}"
        durations = [random.uniform(0.1, 5.0) for _ in range(5)]

        for d in durations:
            self.tracker.record_execution_time(op_name, d)

        self.assertIn(op_name, self.tracker.metrics)
        self.assertEqual(len(self.tracker.metrics[op_name]), len(durations))

        recorded_values = [val for _, val, tags in self.tracker.metrics[op_name]]
        self.assertEqual(recorded_values, durations)

        for _, _, tags in self.tracker.metrics[op_name]:
            self.assertEqual(tags, {"type": "execution_time"})

    def test_record_resource_consumption(self):
        res_name = f"res_{uuid.uuid4().hex}"
        values = [random.uniform(10.0, 100.0) for _ in range(5)]

        for v in values:
            self.tracker.record_resource_consumption(res_name, v)

        self.assertIn(res_name, self.tracker.metrics)
        self.assertEqual(len(self.tracker.metrics[res_name]), len(values))

        recorded_values = [val for _, val, tags in self.tracker.metrics[res_name]]
        self.assertEqual(recorded_values, values)

        for _, _, tags in self.tracker.metrics[res_name]:
            self.assertEqual(tags, {"type": "resource"})

    def test_record_error(self):
        err_type = f"Err_{uuid.uuid4().hex}"
        err_msg = f"Msg_{uuid.uuid4().hex}"

        self.tracker.record_error(err_type, err_msg)
        self.assertEqual(len(self.tracker.errors), 1)

        timestamp, recorded_type, recorded_msg = self.tracker.errors[0]
        self.assertEqual(recorded_type, err_type)
        self.assertEqual(recorded_msg, err_msg)

    def test_get_average_metric(self):
        metric_name = f"metric_{uuid.uuid4().hex}"

        # Проверка пустой метрики
        self.assertEqual(self.tracker.get_average_metric(metric_name), 0.0)

        values = [random.uniform(1.0, 100.0) for _ in range(10)]
        expected_avg = sum(values) / len(values)

        for v in values:
            self.tracker.record_resource_consumption(metric_name, v)

        self.assertAlmostEqual(self.tracker.get_average_metric(metric_name), expected_avg, places=5)

    def test_max_records_limit(self):
        limit = random.randint(3, 8)
        tracker = SystemHealthTracker(max_records=limit)
        op_name = f"op_{uuid.uuid4().hex}"

        for _ in range(limit + 5):
            tracker.record_execution_time(op_name, random.uniform(0.1, 1.0))

        self.assertEqual(len(tracker.metrics[op_name]), limit)

    def test_get_error_frequency(self):
        start_time = random.uniform(1000.0, 5000.0)
        with patch('time.time') as mock_time:
            mock_time.return_value = start_time

            # Запись 3 ошибок в начальный момент времени
            for _ in range(3):
                self.tracker.record_error(f"Err_{uuid.uuid4().hex}", "msg")

            # Сдвиг времени на 10 секунд вперед
            mock_time.return_value = start_time + 10.0

            # Запись еще 2 ошибок
            for _ in range(2):
                self.tracker.record_error(f"Err_{uuid.uuid4().hex}", "msg")

            # Частота за последние 15 секунд: 5 ошибок / 15 сек
            freq_15 = self.tracker.get_error_frequency(15.0)
            self.assertAlmostEqual(freq_15, 5.0 / 15.0, places=5)

            # Частота за последние 5 секунд: 2 ошибки / 5 сек
            freq_5 = self.tracker.get_error_frequency(5.0)
            self.assertAlmostEqual(freq_5, 2.0 / 5.0, places=5)

            # Обработка нулевого временного окна
            self.assertEqual(self.tracker.get_error_frequency(0.0), 0.0)

    def test_analyze_stability_healthy(self):
        op_name = f"op_{uuid.uuid4().hex}"
        val = random.uniform(1.0, 10.0)
        self.tracker.record_execution_time(op_name, val)

        # HEALTHY: <= 10 ошибок
        error_count = random.randint(0, 10)
        for _ in range(error_count):
            self.tracker.record_error("Err", "msg")

        analysis = self.tracker.analyze_stability()
        self.assertEqual(analysis["status"], "HEALTHY")
        self.assertEqual(analysis["total_errors"], error_count)
        self.assertAlmostEqual(analysis["averages"][op_name], val)

    def test_analyze_stability_warning(self):
        # WARNING: > 10 и <= 50 ошибок
        error_count = random.randint(11, 50)
        for _ in range(error_count):
            self.tracker.record_error("Err", "msg")

        analysis = self.tracker.analyze_stability()
        self.assertEqual(analysis["status"], "WARNING")
        self.assertEqual(analysis["total_errors"], error_count)

    def test_analyze_stability_critical(self):
        # CRITICAL: > 50 ошибок
        error_count = random.randint(51, 100)
        for _ in range(error_count):
            self.tracker.record_error("Err", "msg")

        analysis = self.tracker.analyze_stability()
        self.assertEqual(analysis["status"], "CRITICAL")
        self.assertEqual(analysis["total_errors"], error_count)

if __name__ == '__main__':
    unittest.main()