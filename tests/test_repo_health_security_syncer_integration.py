import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.repo_health_security_syncer import RepoHealthSecuritySyncer
from skills.repo_health_diagnostic import RepoHealthDiagnostic
from skills.vulnerability_analyzer import VulnerabilityAnalyzer
from skills.repo_audit_synthesizer import RepoAuditSynthesizer
from skills.repo_logger import RepoLogger

class TestRepoHealthSecuritySyncerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.correlation_id = str(uuid.uuid4())
        self.health_score_input = round(random.uniform(50.0, 100.0), 2)
        self.vulnerability_count_input = random.randint(0, 15)
        
        self.syncer = RepoHealthSecuritySyncer(target_directory=self.test_dir)
        self.diagnostic = RepoHealthDiagnostic()
        self.vuln_analyzer = VulnerabilityAnalyzer()
        self.synthesizer = RepoAuditSynthesizer()
        self.logger = RepoLogger()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_health_security_sync_integration(self):
        env_token = str(uuid.uuid4())
        os.environ["REPO_SYNC_TOKEN"] = env_token

        metric_payload = {
            "sync_id": self.correlation_id,
            "health_score": self.health_score_input,
            "vulnerabilities": self.vulnerability_count_input,
            "token": env_token
        }

        health_diag_result = self.diagnostic.evaluate(self.test_dir, self.health_score_input)
        self.assertIn("status", health_diag_result)

        vuln_analysis_result = self.vuln_analyzer.scan(self.test_dir, self.vulnerability_count_input)
        self.assertIsInstance(vuln_analysis_result, dict)

        sync_result = self.syncer.synchronize(metric_payload)
        
        self.assertIn("synced_id", sync_result)
        self.assertEqual(sync_result["synced_id"], self.correlation_id)
        self.assertTrue(sync_result.get("success", False))

        audit_synthesis = self.synthesizer.build_complex_audit(
            sync_data=sync_result,
            health_metrics=health_diag_result,
            security_metrics=vuln_analysis_result
        )

        self.assertIn("audit_id", audit_synthesis)
        self.assertEqual(audit_synthesis["correlation_id"], self.correlation_id)

        log_record = self.logger.persist_log(
            level="INFO",
            message=f"Integrated sync and audit completed for {self.correlation_id}"
        )
        self.assertIsNotNone(log_record)

        expected_file_name = f"audit_{self.correlation_id}.json"
        expected_file_path = os.path.join(self.test_dir, expected_file_name)
        
        self.assertTrue(
            os.path.exists(expected_file_path),
            f"Real integration artifact not created: {expected_file_path}"
        )

        with open(expected_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.correlation_id, content)
            self.assertIn(str(self.health_score_input), content)

if __name__ == "__main__":
    unittest.main()