import unittest
import os
import shutil
import uuid
import random
import tempfile
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_report_aggregator import AnomalyReportAggregatorError

class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, "repo")
        self.log_path = os.path.join(self.test_dir, "audit.log")
        os.makedirs(self.repo_path)

        self.threshold = random.uniform(0.1, 0.9)
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_full_pipeline_integration(self):
        source_id = str(uuid.uuid4())
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {"event": "test_anomaly", "id": str(uuid.uuid4())}
        telemetry = {"cpu_load": random.random(), "mem_usage": random.random()}

        # 1. Проверка логирования
        log_result = self.hub.log_anomaly(source_id, severity, details, telemetry)
        self.assertTrue(os.path.exists(self.log_path), "Log file was not created")

        # 2. Проверка агрегации
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        value = random.uniform(0.0, 1.0)

        # Если значение выше порога, агрегатор должен обработать его без подавления ошибок
        try:
            self.hub.aggregate_and_report(metric_name, value)
        except AnomalyReportAggregatorError as e:
            self.fail(f"AnomalyAuditHub suppressed or failed to handle aggregation: {e}")

        # 3. Проверка генерации отчета
        report = self.hub.generate_final_report()
        self.assertIsInstance(report, dict, "Report should be a dictionary")

        # Проверка сохранения данных в отчете
        found = False
        if "anomalies" in report:
            for entry in report["anomalies"]:
                if entry.get("source") == source_id:
                    found = True
                    break
        self.assertTrue(found, "The logged anomaly was not found in the final report")

    def test_exception_propagation(self):
        # Проверка, что при некорректных данных агрегатор выбрасывает исключение,
        # а не подавляет его внутри Hub
        with self.assertRaises(Exception):
            # Передача невалидного типа данных для вызова ошибки в агрегаторе
            self.hub.aggregate_and_report(None, "invalid_value")

if __name__ == '__main__':
    unittest.main()