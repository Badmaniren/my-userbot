import unittest
import os
import uuid
import random
import tempfile
from skills.anomaly_report_aggregator import AnomalyReportAggregator
from skills.anomaly_logger import AnomalyLogger
from skills.digest_exporter import DigestExporter


class TestAnomalyReportAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.temp_dir.name, f"anomaly_log_{uuid.uuid4()}.json")
        self.export_path = os.path.join(self.temp_dir.name, f"export_report_{uuid.uuid4()}.json")

        self.logger = AnomalyLogger(log_path=self.log_path)
        self.exporter = DigestExporter(stability_digest=None, anomaly_visualizer=None)

        self.aggregator = AnomalyReportAggregator(
            anomaly_logger=self.logger,
            digest_exporter=self.exporter
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_aggregate_and_export_real_integration(self):
        source_name = f"service_{uuid.uuid4()}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_msg = f"Test anomaly message {uuid.uuid4()}"
        telemetry_data = {"cpu_load": random.uniform(10.0, 99.9), "memory_usage": random.randint(100, 2000)}

        self.logger.log_anomaly(
            source=source_name,
            severity=severity_level,
            details=details_msg,
            telemetry_snapshot=telemetry_data
        )

        aggregated_data = self.aggregator.generate_comprehensive_report()

        self.assertIsNotNone(aggregated_data)

        export_result_path = self.aggregator.export_report(self.export_path)

        self.assertTrue(os.path.exists(export_result_path), "Файл отчета не был создан на диске.")

        with open(export_result_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(source_name, file_content, "Случайный источник аномалии не найден в экспортированном файле.")
            self.assertIn(details_msg, file_content, "Случайные детали аномалии не найдены в экспортированном файле.")


if __name__ == "__main__":
    unittest.main()