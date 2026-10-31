import unittest
import uuid
import random
import tempfile
import shutil
from pathlib import Path

from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError
from skills.git_inspector import GitInspector
from skills.patch_verifier import HypothesisGeneratorError
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyDetectorIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Инициализируем реальный git инспектор без моков
        self.git_inspector = GitInspector(repo_path=self.repo_path)
        
        # Создаем экземпляр AnomalyDetector с реальными зависимостями
        self.threshold = round(random.uniform(1.0, 10.0), 2)
        self.detector = AnomalyDetector(
            repo_path=self.repo_path,
            threshold=self.threshold,
            git_inspector=self.git_inspector
        )
        
        self.log_path = str(Path(self.test_dir) / f"audit_{uuid.uuid4().hex}.log")
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.anomaly_logger = AnomalyLogger(log_path=self.log_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_integration_anomaly_detection_and_logging_pipeline(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        base_value = round(random.uniform(0.1, self.threshold / 2), 2)
        anomaly_value = round(self.threshold * 3.5, 2)
        
        self.detector.record_metric(metric_name, base_value)
        self.detector.record_metric(metric_name, base_value + 0.1)
        
        is_anomaly = self.detector.detect_anomaly(metric_name, anomaly_value)
        self.assertTrue(is_anomaly, "Должна быть обнаружена аномалия по превышению порога")
        
        execution_id = uuid.uuid4().hex
        metrics = {metric_name: anomaly_value}
        analysis_result = self.detector.analyze_execution_metrics(execution_id, metrics)
        
        self.assertEqual(analysis_result["execution_id"], execution_id)
        self.assertIn(metric_name, analysis_result["anomalies_detected"])
        
        severity = "HIGH"
        details = f"Anomaly detected in execution {execution_id} for metric {metric_name} with value {anomaly_value}"
        telemetry_snapshot = {metric_name: anomaly_value, "threshold": self.threshold}
        
        self.audit_hub.log_anomaly(
            source="AnomalyDetector",
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        
        anomalies = self.anomaly_logger.get_anomalies()
        self.assertGreaterEqual(len(anomalies), 1, "Логгер должен зафиксировать записанную аномалию")
        
        latest_anomaly = anomalies[-1]
        self.assertEqual(latest_anomaly.get("source"), "AnomalyDetector")
        self.assertEqual(latest_anomaly.get("severity"), severity)
        self.assertEqual(latest_anomaly.get("details"), details)

    def test_integration_batch_analysis_and_git_inspection(self):
        batch_id = uuid.uuid4().hex
        random_duration = round(self.threshold + random.uniform(1.0, 5.0), 2)
        patch_metrics = [
            {"patch_id": uuid.uuid4().hex, "duration": random_duration},
            {"patch_id": uuid.uuid4().hex, "duration": 0.1}
        ]
        
        batch_result = self.detector.batch_analyze_patches(batch_id, patch_metrics)
        self.assertEqual(batch_result["batch_id"], batch_id)
        self.assertEqual(batch_result["total_analyzed"], 2)
        self.assertEqual(batch_result["anomalies_count"], 1)
        
        repo_analysis = self.detector.detect_anomalies()
        self.assertEqual(repo_analysis["status"], "analyzed")
        self.assertEqual(repo_analysis["repo_path"], self.repo_path)
        self.assertIn("commits_inspected", repo_analysis)

if __name__ == "__main__":
    unittest.main()