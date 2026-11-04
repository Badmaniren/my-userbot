import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_security_gateway import RepoSecurityGateway


class TestRepoSecurityGatewayIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.unique_id = str(uuid.uuid4())
        self.risk_threshold = random.randint(1, 100)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_repo_security_gateway_integration_flow(self):
        req_file = os.path.join(self.test_dir, "requirements.txt")
        dummy_package = f"unsafe-package-{self.unique_id}==1.0.0"
        
        with open(req_file, "w", encoding="utf-8") as f:
            f.write(f"{dummy_package}\n")

        gateway = RepoSecurityGateway(self.test_dir)
        result = gateway.run()

        self.assertIsInstance(result, dict, "Gateway should return a dictionary result.")
        self.assertIn("risk_score", result, "Result must contain 'risk_score'.")
        self.assertIn("status", result, "Result must contain 'status'.")

        risk_score = result.get("risk_score")
        self.assertIsInstance(risk_score, int, "Risk score must be an integer.")

        status = result.get("status")
        if risk_score >= 85:
            self.assertEqual(status, "blocked_by_security_gateway", "High risk score must block the gateway.")
        else:
            self.assertEqual(status, "secure_gateway_passed", "Low risk score should pass the gateway.")
            report_path = result.get("report_path")
            self.assertIsNotNone(report_path, "Passing gateway must generate a report path.")


if __name__ == "__main__":
    unittest.main()