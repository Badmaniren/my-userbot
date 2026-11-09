import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import os
import io
from skills.repo_health_anomaly_remediation_pipeline import (
    AnomalySeverity,
    RemediationExecutionError,
    RepoHealthAnomalyRemediationPipeline,
    run_remediation_pipeline,
    inspect_anomalies
)

class TestRepoHealthAnomalyRemediationPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline_id = uuid.uuid4().hex
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.inspector = MagicMock()
        self.automator = MagicMock()
        self.restorer = MagicMock()
        self.logger = MagicMock()
        self.pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=self.inspector,
            automator=self.automator,
            restorer=self.restorer,
            logger=self.logger
        )

    def test_anomaly_severity_enum(self):
        self.assertEqual(AnomalySeverity.LOW.value, 1)
        self.assertEqual(AnomalySeverity.MEDIUM.value, 2)
        self.assertEqual(AnomalySeverity.HIGH.value, 3)
        self.assertEqual(AnomalySeverity.CRITICAL.value, 4)

    def test_run_pipeline_healthy_repository(self):
        self.inspector.inspect_repository.return_value = None
        result = self.pipeline.run_pipeline(self.repo_path)
        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["status"], "healthy")
        self.assertFalse(result["remediated"])
        self.inspector.inspect_repository.assert_called_once_with(self.repo_path)

    def test_run_pipeline_remediated_successfully(self):
        anomaly_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        anomaly = {"anomaly_id": anomaly_id}
        self.inspector.inspect_repository.return_value = anomaly
        self.automator.execute_remediation.return_value = {"token": token}

        result = self.pipeline.run_pipeline(self.repo_path)

        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["repo_path"], self.repo_path)
        self.assertEqual(result["anomaly_id"], anomaly_id)
        self.assertEqual(result["status"], "remediated")
        self.assertEqual(result["token"], token)
        self.automator.execute_remediation.assert_called_once_with(self.repo_path, anomaly)

    def test_run_pipeline_remediation_failure_triggers_restorer(self):
        anomaly_id = uuid.uuid4().hex
        anomaly = {"anomaly_id": anomaly_id}
        self.inspector.inspect_repository.return_value = anomaly
        error_message = uuid.uuid4().hex
        self.automator.execute_remediation.side_effect = Exception(error_message)

        with self.assertRaises(RemediationExecutionError) as ctx:
            self.pipeline.run_pipeline(self.repo_path)

        self.assertIn(error_message, str(ctx.exception))
        self.restorer.restore_state.assert_called_once_with(self.repo_path, anomaly_id)

    def test_analyze_anomaly_stream(self):
        log_path = f"/tmp/{uuid.uuid4().hex}.log"
        metric_name = uuid.uuid4().hex
        threshold = random.uniform(1.0, 100.0)
        random_content = uuid.uuid4().hex.encode('utf-8')

        with patch("builtins.open", return_value=io.BytesIO(random_content) if False else io.StringIO(uuid.uuid4().hex)) as mock_file:
            result = self.pipeline.analyze_anomaly_stream(log_path, metric_name, threshold)
            self.assertTrue(result["stream_processed"])
            self.assertEqual(result["metric"], metric_name)
            self.assertIsInstance(result["anomaly_score"], float)

    def test_batch_remediate(self):
        repo_paths = [f"/tmp/{uuid.uuid4().hex}" for _ in range(3)]
        self.inspector.inspect_repository.return_value = None

        reports = self.pipeline.batch_remediate(repo_paths)
        self.assertEqual(len(reports), 3)
        for report in reports:
            self.assertEqual(report["status"], "healthy")

    def test_run_remediation_pipeline_function(self):
        run_id = uuid.uuid4().hex
        target_path = f"/tmp/{uuid.uuid4().hex}"
        os.makedirs(target_path, exist_ok=True)
        payload = {
            "run_id": run_id,
            "target_path": target_path
        }

        try:
            result = run_remediation_pipeline(payload)
            self.assertEqual(result["run_id"], run_id)
            self.assertEqual(result["status"], "remediated")
            marker_path = os.path.join(target_path, f".remediated_{run_id}")
            self.assertTrue(os.path.exists(marker_path))
        finally:
            if os.path.exists(target_path):
                for f in os.listdir(target_path):
                    os.remove(os.path.join(target_path, f))
                os.rmdir(target_path)

    def test_inspect_anomalies_function(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"
        os.makedirs(target_path, exist_ok=True)
        run_id = uuid.uuid4().hex
        marker_path = os.path.join(target_path, f".remediated_{run_id}")
        
        with open(marker_path, "w") as f:
            f.write(uuid.uuid4().hex)

        try:
            payload = {"target_path": target_path}
            res = inspect_anomalies(payload)
            self.assertFalse(res["anomaly_detected"])
        finally:
            if os.path.exists(marker_path):
                os.remove(marker_path)
            if os.path.exists(target_path):
                os.rmdir(target_path)

    def test_inspect_anomalies_no_remediation(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"
        os.makedirs(target_path, exist_ok=True)
        try:
            payload = {"target_path": target_path}
            res = inspect_anomalies(payload)
            self.assertTrue(res["anomaly_detected"])
        finally:
            if os.path.exists(target_path):
                os.rmdir(target_path)

if __name__ == "__main__":
    unittest.main()