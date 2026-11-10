import unittest
import os
import tempfile
import shutil
import uuid
import random

from skills.repo_health_anomaly_remediation_pipeline import (
    RepoHealthAnomalyRemediationPipeline,
    RemediationExecutionError,
    run_remediation_pipeline,
    inspect_anomalies
)
from skills.repo_health_anomaly_inspector import inspect_repository as real_inspect_repository
from skills.repo_health_automator import execute_remediation as real_execute_remediation
from skills.repo_health_restorer import restore_state as real_restore_state
from skills.repo_logger import log_event as real_log_event

class RealInspectorAdapter:
    def inspect_repository(self, repo_path):
        payload = {"target_path": repo_path}
        res = inspect_anomalies(payload)
        if res.get("anomaly_detected"):
            return {"anomaly_id": f"anomaly_{uuid.uuid4().hex[:8]}"}
        return None

class RealAutomatorAdapter:
    def execute_remediation(self, repo_path, anomaly):
        run_id = uuid.uuid4().hex[:8]
        payload = {"target_path": repo_path, "run_id": run_id}
        res = run_remediation_pipeline(payload)
        return {"token": res.get("run_id")}

class RealRestorerAdapter:
    def restore_state(self, repo_path, anomaly_id):
        if os.path.exists(repo_path):
            for f in os.listdir(repo_path):
                if f.startswith(".remediated_"):
                    try:
                        os.remove(os.path.join(repo_path, f))
                    except Exception:
                        pass
        return {"restored": True, "anomaly_id": anomaly_id}

class RealLoggerAdapter:
    def log(self, message):
        try:
            real_log_event({"message": message})
        except Exception:
            pass

class TestRepoHealthAnomalyRemediationPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pipeline_id = f"pipe_{uuid.uuid4().hex[:6]}"
        self.inspector = RealInspectorAdapter()
        self.automator = RealAutomatorAdapter()
        self.restorer = RealRestorerAdapter()
        self.logger = RealLoggerAdapter()

        self.pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=self.inspector,
            automator=self.automator,
            restorer=self.restorer,
            logger=self.logger
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_integration_full_remediation_cycle(self):
        result = self.pipeline.run_pipeline(self.test_dir)
        
        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("status"), "remediated")
        self.assertIsNotNone(result.get("token"))
        self.assertIsNotNone(result.get("anomaly_id"))
        
        files = os.listdir(self.test_dir)
        remediated_files = [f for f in files if f.startswith(".remediated_")]
        self.assertTrue(len(remediated_files) > 0)

    def test_integration_healthy_repository(self):
        run_id = uuid.uuid4().hex[:8]
        marker_path = os.path.join(self.test_dir, f".remediated_{run_id}")
        with open(marker_path, "w") as f:
            f.write("already clean")

        result = self.pipeline.run_pipeline(self.test_dir)
        
        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("status"), "healthy")
        self.assertFalse(result.get("remediated"))

    def test_integration_batch_remediate(self):
        dirs = []
        for _ in range(random.randint(2, 4)):
            d = tempfile.mkdtemp(dir=self.test_dir)
            dirs.append(d)

        reports = self.pipeline.batch_remediate(dirs)
        self.assertEqual(len(reports), len(dirs))
        for rep in reports:
            self.assertEqual(rep.get("status"), "remediated")

    def test_integration_anomaly_stream_analysis(self):
        log_file = os.path.join(self.test_dir, f"log_{uuid.uuid4().hex}.txt")
        random_content = "".join(random.choices("ABCDEF0