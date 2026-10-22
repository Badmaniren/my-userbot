import unittest
import os
import shutil
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_env_{uuid.uuid4().hex}"
        self.log_path = os.path.join(self.test_dir, "audit.log")
        self.repo_path = os.path.join(self.test_dir, "repo")
        os.makedirs(self.repo_path, exist_ok=True)

        self.threshold = random.uniform(0.1, 0.9)
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_full_audit_pipeline_integration(self):
        # Генерируем случайные данные для теста
        source_id = f"source_{uuid.uuid4().hex[:8]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {"error_code": random.randint(100, 999), "msg": "integration_test"}
        telemetry = {"cpu_load": random.random(), "mem_usage": random.random()}

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = random.uniform(0.0, 1.0)

        # 1. Проверка логирования
        log_result = self.hub.log_anomaly(source_id, severity, details, telemetry)
        self.assertTrue(os.path.exists(self.log_path), "Лог-файл не был создан")

        # 2. Проверка агрегации
        agg_result = self.hub.aggregate_and_report(metric_name, metric_value)
        self.assertIsNotNone(agg_result, "Агрегатор не вернул результат")

        # 3. Проверка генерации отчета
        final_report = self.hub.generate_final_report()
        self.assertIsInstance(final_report, dict, "Финальный отчет должен быть словарем")

        # Проверка сохранения данных в структуре отчета
        # Проверяем, что данные из лога попали в отчет через агрегатор
        found_in_report = False
        if "anomalies" in final_report:
            for entry in final_report["anomalies"]:
                if entry.get("source") == source_id:
                    found_in_report = True
                    break

        self.assertTrue(found_in_report, "Данные аномалии не найдены в финальном отчете")

    def test_exception_stability_on_invalid_data(self):
        # Проверка стабильности при передаче некорректных данных
        try:
            self.hub.aggregate_and_report("invalid_metric", -999.0)
        except Exception as e:
            self.fail(f"Hub выбросил исключение при обработке граничных значений: {e}")

if __name__ == "__main__":
    unittest.main()