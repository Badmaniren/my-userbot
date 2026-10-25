import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_autofixer_engine import (
    AnomalyLogger,
    AnomalyAuditHub,
    ExtractorTool,
    GitInspector,
    start_new
)

class TestAnomalyAutofixerEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, f"test_anomaly_{uuid.uuid4()}.log")
        self.repo_path = self.test_dir.name

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_anomaly_flow(self):
        # 1. Генерация случайных данных для теста
        source_name = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"cpu_load_{uuid.uuid4().hex[:4]}"
        metric_value = round(random.uniform(10.0, 100.0), 2)
        threshold_value = 50.0

        telemetry_data = {
            "node_id": str(uuid.uuid4()),
            "memory_usage": random.randint(1024, 8192),
            "active_threads": random.randint(1, 64)
        }

        # 2. Инициализация компонентов без моков
        logger = AnomalyLogger(log_path=self.log_path)
        logger.clear_logs()

        hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=threshold_value
        )

        # 3. Интеграционный шаг: логирование аномалии через Hub (который использует AnomalyLogger)
        hub.log_anomaly(
            source=source_name,
            severity=severity_level,
            details=f"Anomaly detected in {source_name}",
            telemetry_snapshot=telemetry_data
        )

        # 4. Проверка записи логов
        anomalies = logger.get_anomalies()
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["source"], source_name)
        self.assertEqual(anomalies[0]["severity"], severity_level)
        self.assertEqual(anomalies[0]["telemetry_snapshot"], telemetry_data)

        # 5. Интеграционный шаг: агрегация метрик через Hub
        audit_result = hub.aggregate_and_report(metric_name, metric_value)
        self.assertEqual(audit_result["metric_name"], metric_name)
        self.assertEqual(audit_result["value"], metric_value)
        expected_status = "EXCEEDS_THRESHOLD" if metric_value > threshold_value else "NORMAL"
        self.assertEqual(audit_result["status"], expected_status)

        # 6. Проверка генерации финального отчета
        final_report = hub.generate_final_report()
        self.assertEqual(final_report["repo_path"], self.repo_path)
        self.assertEqual(final_report["threshold"], threshold_value)
        self.assertGreaterEqual(len(final_report["metrics"]), 1)
        self.assertEqual(final_report["logs"]["total_anomalies"], 1)

        # 7. Проверка вспомогательных инструментов (ExtractorTool и GitInspector)
        extractor = ExtractorTool()
        random_tag = f"tag-{uuid.uuid4().hex[:6]}"
        random_attr_val = uuid.uuid4().hex[:8]
        markup = f'<{random_tag} id="{random_attr_val}"></{random_tag}>'
        extracted = extractor.extract(markup)
        self.assertIn(random_tag, extracted)
        self.assertEqual(extracted[random_tag].get("id"), random_attr_val)

        git_inspector = GitInspector(repo_path=self.repo_path)
        repo_analysis = git_inspector.analyze_repository()
        self.assertIn("repo_path", repo_analysis)
        self.assertIn("recent_commits", repo_analysis)

        # 8. Проверка стартовой функции модуля
        payload_data = {"session_id": str(uuid.uuid4())}
        start_response = start_new(payload_data)
        self.assertEqual(start_response["status"], "started")
        self.assertEqual(start_response["payload"], payload_data)

if __name__ == "__main__":
    unittest.main()