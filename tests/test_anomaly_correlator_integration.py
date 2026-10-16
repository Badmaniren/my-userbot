import unittest
import tempfile
import shutil
import uuid
import random
import os

from skills.anomaly_detector import AnomalyDetector
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_correlator import AnomalyCorrelator


class TestAnomalyCorrelatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, f"anomalies_{uuid.uuid4().hex}.json")
        
        self.detector = AnomalyDetector(repo_path=self.test_dir, threshold=0.5)
        self.logger = AnomalyLogger(log_path=self.log_file)
        
        self.correlator = AnomalyCorrelator(
            detector=self.detector,
            logger=self.logger
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_end_to_end_anomaly_correlation(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        normal_value = round(random.uniform(1.0, 10.0), 2)
        anomaly_value = round(random.uniform(50.0, 100.0), 2)
        
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        source_name = f"source_{uuid.uuid4().hex[:6]}"
        
        self.detector.record_metric(metric_name, normal_value)
        self.detector.record_metric(metric_name, normal_value)
        
        is_anomaly = self.detector.detect_anomaly(metric_name, anomaly_value)
        self.assertTrue(is_anomaly, "Детектор должен зафиксировать аномалию на резко отличающемся значении")
        
        telemetry_data = {
            "uuid": str(uuid.uuid4()),
            "metric": metric_name,
            "value": anomaly_value
        }
        self.logger.log_anomaly(
            source=source_name,
            severity=severity,
            details={"description": "Test anomaly injection"},
            telemetry_snapshot=telemetry_data
        )
        
        correlation_result = self.correlator.correlate_events()
        
        self.assertIsNotNone(correlation_result, "Коррелятор должен вернуть результат анализа")
        
        logged_anomalies = self.logger.get_anomalies()
        self.assertGreaterEqual(len(logged_anomalies), 1, "Логгер должен содержать записанную аномалию")
        
        report = self.logger.get_structured_report()
        self.assertIsNotNone(report, "Структурированный отчет от логгера не должен быть пустым")

if __name__ == "__main__":
    unittest.main()