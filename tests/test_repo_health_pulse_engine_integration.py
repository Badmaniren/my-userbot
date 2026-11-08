import unittest
import uuid
import random
import tempfile
import os
from skills.repo_health_pulse_engine import (
    RepoHealthPulseEngine,
    RepoMonitor,
    RepoLogger,
    RepoAnalytics,
    PulseMetric,
    PulseException
)

class TestRepoHealthPulseEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.engine = RepoHealthPulseEngine()
        self.monitor = RepoMonitor()
        self.logger = RepoLogger()
        self.analytics = RepoAnalytics()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_full_pulse_lifecycle_integration(self):
        rand_repo_id = f"repo-{uuid.uuid4()}"
        rand_metric_name = f"metric-{random.randint(1000, 9999)}"
        rand_run_id = f"run-{uuid.uuid4()}"
        rand_path = os.path.join(self.temp_dir.name, f"{uuid.uuid4()}.txt")
        rand_log_msg = f"Integration log message {uuid.uuid4()}"

        # 1. Проверяем мониторинг состояния через RepoMonitor (взаимодействие навыков)
        status_result = self.monitor.check_status(rand_path)
        self.assertEqual(status_result["status"], "ok")
        self.assertEqual(status_result["path"], rand_path)

        # 2. Собираем метрику через движок пульса
        metric_obj = self.engine.collect_metric(rand_repo_id, rand_metric_name)
        self.assertIsInstance(metric_obj, PulseMetric)
        self.assertEqual(metric_obj.repo_id, rand_repo_id)
        self.assertEqual(metric_obj.name, rand_metric_name)
        self.assertTrue(metric_obj.is_healthy)

        # 3. Логируем событие через RepoLogger с реальной записью на диск
        log_success = self.logger.log_event(rand_path, rand_log_msg)
        self.assertTrue(log_success)
        self.assertTrue(os.path.exists(rand_path))

        # 4. Читаем поток через monitor_stream движка
        stream_lines = self.engine.monitor_stream(rand_path, limit=10)
        self.assertIn(rand_log_msg, stream_lines)

        # 5. Генерируем аналитический отчет через RepoAnalytics
        report_result = self.analytics.generate_metrics_report(rand_path)
        self.assertEqual(report_result["report"], "generated")
        self.assertEqual(report_result["path"], rand_path)

        # 6. Обрабатываем и собираем итоговый пульс
        processed_pulse = self.engine.collect_and_process_pulse(
            repo_path=rand_path,
            run_id=rand_run_id,
            metric=metric_obj
        )
        self.assertEqual(processed_pulse["status"], "success")
        self.assertEqual(processed_pulse["run_id"], rand_run_id)
        self.assertEqual(processed_pulse["metric"], metric_obj)
        self.assertEqual(processed_pulse["repo_path"], rand_path)

    def test_export_pulse_exception_handling(self):
        invalid_url = f"http://localhost:{random.randint(10000, 65535)}/{uuid.uuid4()}"
        payload = {"test_id": str(uuid.uuid4()), "value": random.random()}

        with self.assertRaises(PulseException):
            self.engine.export_pulse(invalid_url, payload)

if __name__ == "__main__":
    unittest.main()