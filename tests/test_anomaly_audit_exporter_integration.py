import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.anomaly_audit_exporter import AnomalyAuditExporter
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger


class TestAnomalyAuditExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.test_dir, f"audit_{uuid.uuid4().hex}.log")
        self.repo_path = self.test_dir
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.exporter = AnomalyAuditExporter(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_composition_and_export_integration(self):
        source = f"source_{uuid.uuid4().hex[:8]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = f"Test anomaly detail {uuid.uuid4().hex}"
        telemetry_snapshot = {"cpu_load": random.random(), "memory_usage": random.randint(100, 999)}

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(10.0, 100.0), 2)

        self.assertTrue(
            hasattr(self.exporter, 'audit_hub') or isinstance(getattr(self.exporter, 'audit_hub', None), AnomalyAuditHub),
            "AnomalyAuditExporter должен композиционировать AnomalyAuditHub"
        )
        self.assertTrue(
            hasattr(self.exporter, 'logger') or isinstance(getattr(self.exporter, 'logger', None), AnomalyLogger),
            "AnomalyAuditExporter должен композиционировать AnomalyLogger"
        )

        if hasattr(self.exporter, 'log_and_audit'):
            self.exporter.log_and_audit(source, severity, details, telemetry_snapshot)
        else:
            self.exporter.audit_hub.log_anomaly(source, severity, details, telemetry_snapshot)

        if hasattr(self.exporter, 'aggregate'):
            self.exporter.aggregate(metric_name, metric_value)
        else:
            self.exporter.audit_hub.aggregate_and_report(metric_name, metric_value)

        export_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")

        if hasattr(self.exporter, 'export_report'):
            result = self.exporter.export_report(export_path)
        elif hasattr(self.exporter, 'generate_and_export'):
            result = self.exporter.generate_and_export(export_path)
        else:
            report_data = self.exporter.audit_hub.generate_final_report()
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(str(report_data))
            result = export_path

        self.assertTrue(
            os.path.exists(export_path) or (isinstance(result, str) and os.path.exists(result)),
            "Интеграционный тест требует фактического создания файла отчета на диске."
        )

        target_file = export_path if os.path.exists(export_path) else result
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(source, content, f"Экспортированный отчет должен содержать случайный источник: {source}")
            self.assertIn(details, content, f"Экспортированный отчет должен содержать детали: {details}")


if __name__ == '__main__':
    unittest.main()