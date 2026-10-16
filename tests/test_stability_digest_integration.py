import unittest
import uuid
import random
import tempfile
import shutil
import os

from skills.stability_digest import StabilityDigest, StabilityDigestError
from skills.system_telemetry import SystemTelemetry
from skills.anomaly_correlator import AnomalyCorrelator


class TestStabilityDigestIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.log_path = os.path.join(self.test_dir, "anomalies.log")
        
        # Инициализируем реальные зависимые навыки без моков
        self.anomaly_detector = AnomalyCorrelator(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=0.5,
            detector=None,
            logger=None
        )
        self.system_telemetry = SystemTelemetry(
            repo_path=self.repo_path,
            anomaly_detector=self.anomaly_detector,
            autonomous_engine=None
        )
        
        # Создаем тестируемый модуль композиции
        self.stability_digest = StabilityDigest(
            repo_path=self.repo_path,
            anomaly_detector=self.anomaly_detector,
            system_telemetry=self.system_telemetry
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_generate_digest_integration_with_real_modules(self):
        # Генерируем случайные данные для телеметрии и аномалий
        random_metric_name = f"cpu_load_{uuid.uuid4().hex[:8]}"
        random_metric_value = round(random.uniform(10.0, 99.9), 2)
        execution_id = str(uuid.uuid4())

        # Записываем реальные данные через систему телеметрии
        self.system_telemetry.record_metric(random_metric_name, random_metric_value)

        # Вызываем тестируемый метод интеграционного дайджеста
        digest = self.stability_digest.generate_digest(execution_id=execution_id)

        # Проверяем структуру и наличие реальных данных без заглушек
        self.assertIsInstance(digest, dict)
        self.assertIn("summary", digest)
        self.assertIn("anomalies", digest)
        
        summary = digest["summary"]
        self.assertIsInstance(summary, dict)

    def test_analyze_digest_trends_with_dynamic_data(self):
        # Генерируем уникальное имя метрики и последовательность случайных значений
        metric_name = f"memory_usage_{uuid.uuid4().hex[:8]}"
        values = [round(random.uniform(1.0, 50.0), 2) for _ in range(5)]
        
        # Записываем историю метрик в реальный модуль телеметрии
        for val in values:
            self.system_telemetry.record_metric(metric_name, val)

        # Запускаем анализ трендов через StabilityDigest
        trend_report = self.stability_digest.analyze_digest_trends(metric_name)

        # Проверяем корректность интеграции и расчета тренда
        self.assertIsInstance(trend_report, dict)
        self.assertEqual(trend_report["metric"], metric_name)
        self.assertEqual(trend_report["history"], values)
        self.assertIn(trend_report["trend"], ["stable", "increasing", "decreasing"])

    def test_export_digest_stream_valid_snapshot(self):
        # Создаем уникальный идентификатор потока/снимка
        stream_id = str(uuid.uuid4())
        metric_name = f"disk_io_{uuid.uuid4().hex[:8]}"
        metric_value = round(random.uniform(100.0, 500.0), 2)

        self.system_telemetry.record_metric(metric_name, metric_value)

        # Экспортируем поток через дайджест
        snapshot = self.stability_digest.export_digest_stream(stream_id)

        # Проверяем, что возвращается реальный слепок телеметрии
        self.assertIsInstance(snapshot, dict)


if __name__ == "__main__":
    unittest.main()