import unittest
import os
import uuid
import random
import json
from skills.remediation_telemetry_reporter import RemediationTelemetryReporter
from skills.vulnerability_remediation_metrics_collector import VulnerabilityRemediationMetricsCollector
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector

class TestRemediationTelemetryReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.reporter = RemediationTelemetryReporter()
        self.metrics_collector = VulnerabilityRemediationMetricsCollector()
        self.health_collector = SystemHealthTelemetryCollector()

        self.test_dir = f"test_artifacts_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)

        self.pipeline_id = str(uuid.uuid4())
        self.report_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            for f in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, f))
            os.rmdir(self.test_dir)

    def test_full_remediation_telemetry_integration(self):
        # Генерируем случайные данные для процесса
        metric_val = random.uniform(0.1, 99.9)
        incident_id = str(uuid.uuid4())

        # 1. Используем VulnerabilityRemediationMetricsCollector для сбора метрик
        self.metrics_collector.collect_metric(self.pipeline_id, "patch_latency", metric_val)
        aggregated_metrics = self.metrics_collector.aggregate_pipeline_metrics(
            self.pipeline_id,
            [{"name": "patch_latency", "value": metric_val}]
        )

        # 2. Вызываем тестируемый модуль, который связывает метрики с состоянием системы
        # Модуль должен использовать SystemHealthTelemetryCollector внутри себя
        result = self.reporter.generate_unified_report(
            pipeline_id=self.pipeline_id,
            incident_data={"id": incident_id, "severity": "high"},
            metrics=aggregated_metrics,
            output_path=self.report_path
        )

        # 3. Проверка: файл отчета должен быть создан
        self.assertTrue(os.path.exists(self.report_path), "Отчет не был создан в файловой системе")

        # 4. Проверка содержимого отчета
        with open(self.report_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data['pipeline_id'], self.pipeline_id)
            self.assertEqual(data['incident_id'], incident_id)
            self.assertIn('health_status', data)

        # 5. Проверка интеграции через SystemHealthTelemetryCollector
        # Проверяем, что данные были корректно обработаны через метод сбора
        health_check = self.health_collector.collect_and_aggregate_telemetry(
            module_name="remediation_reporter",
            incident_data={"id": incident_id},
            audit_summary="success",
            metrics=aggregated_metrics,
            dashboard_format="json",
            incidents_list=[incident_id],
            patches_list=[self.pipeline_id]
        )

        self.assertIsNotNone(health_check)
        self.assertIn(self.pipeline_id, str(health_check))

if __name__ == '__main__':
    unittest.main()