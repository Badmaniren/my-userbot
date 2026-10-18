import unittest
import uuid
import random
import tempfile
import shutil
from pathlib import Path

from skills.anomaly_detector import AnomalyDetector
from skills.anomaly_reactor import AutonomousReactorEngine
from skills.git_inspector import GitInspector
from skills.anomaly_guardian import AnomalyGuardian


class TestAnomalyGuardianIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        # Инициализируем реальные компоненты без моков согласно требованиям архитектора
        self.git_inspector = GitInspector(repo_path=self.repo_path)
        self.detector = AnomalyDetector(
            repo_path=self.repo_path,
            threshold=0.5,
            git_inspector=self.git_inspector,
            patch_verifier=None
        )
        self.reactor = AutonomousReactorEngine()

        # Создаем тестируемый защитный контур (композиция детектор + реактор)
        self.guardian = AnomalyGuardian(detector=self.detector, reactor=self.reactor)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_preventive_suppression_circuit(self):
        # Генерируем уникальные динамические данные для исключения хардкода
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        random_spike_value = float(random.randint(100, 1000))
        normal_value = float(random.randint(1, 10))

        execution_id = uuid.uuid4().hex

        # Записываем нормальные метрики для калибровки порога
        for _ in range(5):
            self.detector.record_metric(metric_name, normal_value)

        # Фиксируем аномальный скачок, который должен активировать детектор
        self.detector.record_metric(metric_name, random_spike_value)

        is_anomaly = self.detector.detect_anomaly(metric_name, random_spike_value)
        self.assertTrue(is_anomaly, "Детектор должен распознать аномалию по заданному порогу")

        # Проверяем сквозной интеграционный вызов через AnomalyGuardian
        # Контур должен принять аномалию, проанализировать и передать в автономный реактор
        execution_metrics = {
            metric_name: random_spike_value,
            "error_rate": random.uniform(0.8, 1.0)
        }

        analysis_result = self.detector.analyze_execution_metrics(execution_id, execution_metrics)
        if isinstance(analysis_result, dict) and "anomalies_detected" in analysis_result:
            self.assertIn(metric_name, analysis_result["anomalies_detected"], "Анализ метрик выполнения должен содержать проверяемую метрику")
        else:
            self.assertIn(metric_name, analysis_result, "Анализ метрик выполнения должен содержать проверяемую метрику")

        # Вызываем защитный контур (AnomalyGuardian), связывающий детектор и реактор
        guard_response = self.guardian.process_and_mitigate(
            metric_name=metric_name,
            target_value=random_spike_value,
            execution_id=execution_id,
            metrics=execution_metrics
        )

        # Проверяем реальный результат работы контура превентивного подавления
        self.assertIsInstance(guard_response, dict, " guardian должен возвращать структурированный словарь ответа")
        self.assertIn("mitigated", guard_response, "Ответ должен содержать статус подавления аномалии")
        self.assertTrue(guard_response["mitigated"], "Автономный контур должен успешно подавить обнаруженную аномалию")

        # Убеждаемся, что история метрик сохранилась корректно
        history = self.detector.get_metric_history(metric_name)
        self.assertGreaterEqual(len(history), 6, "История метрик должна содержать все записанные точки данных")
        self.assertIn(random_spike_value, history, "Аномальное значение должно быть зафиксировано в истории")