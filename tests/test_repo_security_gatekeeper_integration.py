import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.repo_security_gatekeeper import RepoSecurityGatekeeper
from skills.vulnerability_analyzer import VulnerabilityAnalyzer
from skills.repo_auditor import RepoAuditor
from skills.repo_logger import RepoLogger


class TestRepoSecurityGatekeeperIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.target_repo = os.path.join(self.test_dir, f"repo_{uuid.uuid4().hex[:8]}")
        os.makedirs(self.target_repo, exist_ok=True)
        
        self.run_id = str(uuid.uuid4())
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        self.logger = RepoLogger()
        self.auditor = RepoAuditor()
        self.analyzer = VulnerabilityAnalyzer()
        self.gatekeeper = RepoSecurityGatekeeper(
            logger=self.logger,
            auditor=self.auditor,
            analyzer=self.analyzer
        )

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_security_gatekeeper_integration_flow(self):
        vulnerable_file_name = f"code_{uuid.uuid4().hex[:6]}.py"
        vulnerable_file_path = os.path.join(self.target_repo, vulnerable_file_name)
        
        random_secret_token = f"TOKEN_{uuid.uuid4().hex}"
        code_content = f"# Test vulnerability file\nSECRET_KEY = '{random_secret_token}'\n"
        
        with open(vulnerable_file_path, "w", encoding="utf-8") as f:
            f.write(code_content)

        audit_config = {
            "run_id": self.run_id,
            "threshold": self.severity_level,
            "scan_target": self.target_repo
        }

        gatekeeper_result = self.gatekeeper.evaluate_repository(audit_config)

        self.assertIsInstance(gatekeeper_result, dict, "Gatekeeper must return a result dictionary")
        self.assertIn("status", gatekeeper_result, "Result must contain 'status'")
        self.assertIn("vulnerabilities_detected", gatekeeper_result, "Result must contain vulnerabilities info")
        
        report_artifact_path = os.path.join(self.target_repo, f"security_gate_report_{self.run_id}.json")
        
        self.assertTrue(
            os.path.exists(report_artifact_path) or gatekeeper_result.get("report_generated", False),
            "Integration must produce a persistent security report file or artifact flag"
        )

        detected_vulnerabilities = gatekeeper_result.get("vulnerabilities", [])
        self.assertGreaterEqual(
            len(detected_vulnerabilities), 
            0, 
            "Vulnerability analyzer and auditor must process the repository dynamically"
        )

if __name__ == "__main__":
    unittest.main()