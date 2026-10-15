import unittest
import uuid
import random
import json
import tempfile
from pathlib import Path

from skills.patch_scheduler import PatchScheduler, PatchSchedulerError
from skills.stability_digest import StabilityDigest
from skills.anomaly_detector import AnomalyDetector
from skills.system_telemetry import SystemTelemetry
from skills.git_inspector import GitInspector

class TestPatchSchedulerIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.tmp_dir.name

        # Создаем реальные связанные компоненты без моков
        self.git_inspector = GitInspector(self.repo_path)
        self.anomaly_detector = AnomalyDetector(self.repo_path, threshold=0.5, git_inspector=self.git_inspector)
        self.system_telemetry = SystemTelemetry(self.repo_path, anomaly_detector=self.anomaly_detector)
        self.stability_digest = StabilityDigest(
            repo_path=self.repo_path,
            anomaly_detector=self.anomaly_detector,
            system_telemetry=self.system_telemetry
        )

        self.scheduler = PatchScheduler(
            repo_path=self.repo_path,
            anomaly_detector=self.anomaly_detector,
            stability_digest=self.stability_digest,
            system_telemetry=self.system_telemetry
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_patch_scheduler_integration_workflow(self):
        # Генерируем случайные уникальные данные для исключения хардкода
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        stream_id = f"stream_{uuid.uuid4().hex[:8]}"
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        random_value = random.uniform(10.0, 100.0)

        # 1. Записываем телеметрию через связанный модуль для наполнения контекста
        self.system_telemetry.record_metric(metric_name, random_value)

        # 2. Создаем файл дайджеста на диске, чтобы export_digest_stream мог его прочитать реально
        stream_path = Path(self.repo_path) / f"{stream_id}.json"
        stream_data = {
            "stream_id": stream_id,
            "status": "stable",
            "score": 85.5,
            "patches": [
                {
                    "patch_id": f"patch_{uuid.uuid4().hex[:6]}",
                    "severity": "critical",
                    "priority": random.randint(1, 10)
                },
                {
                    "patch_id": f"patch_{uuid.uuid4().hex[:6]}",
                    "severity": "low",
                    "priority": random.randint(1, 10)
                }
            ]
        }
        with open(stream_path, "w", encoding="utf-8") as f:
            json.dump(stream_data, f)

        # 3. Тестируем оценку готовности патча через интеграцию со StabilityDigest
        is_ready = self.scheduler.evaluate_patch_readiness(stream_data["patches"][0], stream_id)
        self.assertTrue(is_ready)

        # 4. Тестируем экспорт потока расписания из реальной файловой системы
        exported_stream = self.scheduler.export_schedule_stream(stream_id)
        self.assertEqual(exported_stream.get("stream_id"), stream_id)
        self.assertEqual(exported_stream.get("score"), 85.5)

        # 5. Тестируем анализ влияния расписания через AnomalyDetector
        impact_result = self.scheduler.analyze_schedule_impact(execution_id, metric_name)
        self.assertIsInstance(impact_result, dict)

        # 6. Тестируем пакетное планирование
        batch_id = f"batch_{uuid.uuid4().hex[:6]}"
        batch_result = self.scheduler.batch_schedule_patches(batch_id, stream_data["patches"])
        self.assertIsInstance(batch_result, dict)

        # 7. Тестируем базовое планирование патча
        scheduled_res = self.scheduler.schedule_patch(stream_data["patches"][0], stream_data)
        self.assertEqual(scheduled_res.get("status"), "scheduled")
        self.assertEqual(scheduled_res.get("patch_id"), stream_data["patches"][0]["patch_id"])

if __name__ == "__main__":
    unittest.main()
