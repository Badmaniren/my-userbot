import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.repo_audit_synthesizer import RepoAuditSynthesizer
from skills.repo_auditor import RepoAuditor
from skills.repo_performance_profiler_pipeline import RepoPerformanceProfilerPipeline
from skills.repo_health_diagnostic import RepoHealthDiagnostic
from skills.repo_security_gateway import RepoSecurityGateway


class TestRepoAuditSynthesizerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.synthesizer = RepoAuditSynthesizer()
        self.auditor = RepoAuditor()
        self.profiler = RepoPerformanceProfilerPipeline()
        self.diagnostic = RepoHealthDiagnostic()
        self.security_gateway = RepoSecurityGateway()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_synthesize_repository_audit_real_flow(self):
        run_id = str(uuid.uuid4())
        mock_metric_value = random.randint(10, 100)
        
        test_file_path = os.path.join(self.test_dir, f"test_target_{run_id}.py")
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Target file for audit run {run_id}\n")
            f.write(f"PERFORMANCE_WEIGHT = {mock_metric_value}\n")

        security_result = self.security_gateway.evaluate(self.test_dir)
        health_result = self.diagnostic.run_diagnostic(self.test_dir)
        performance_result = self.profiler.execute(self.test_dir)
        base_audit = self.auditor.audit(self.test_dir)

        synthetic_payload = {
            "run_id": run_id,
            "target_path": self.test_dir,
            "security": security_result,
            "health": health_result,
            "performance": performance_result,
            "base_audit": base_audit,
            "random_seed": random.random()
        }

        synthesis_result = self.synthesizer.synthesize(synthetic_payload)

        self.assertIsInstance(synthesis_result, dict)
        self.assertIn("unified_slice", synthesis_result)
        
        slice_data = synthesis_result["unified_slice"]
        self.assertEqual(slice_data.get("run_id"), run_id)
        self.assertIn("metrics", slice_data)
        
        report_filename = f"audit_report_{run_id}.json"
        saved_report_path = self.synthesizer.export_report(self.test_dir, synthesis_result, report_filename)
        
        full_path = os.path.join(self.test_dir, report_filename)
        self.assertTrue(os.path.exists(full_path))
        self.assertEqual(saved_report_path, full_path)

        with open(full_path, "r", encoding="utf-8") as rf:
            content = rf.read()
            self.assertIn(run_id, content)


if __name__ == "__main__":
    unittest.main()