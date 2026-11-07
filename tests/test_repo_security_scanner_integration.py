import unittest
import uuid
import os
import tempfile
from skills.repo_security_scanner import repo_security_scanner
from skills.vulnerability_analyzer import vulnerability_analyzer


class TestRepoSecurityScannerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.scan_uuid = str(uuid.uuid4())
        self.severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def tearDown(self):
        self.test_dir.cleanup()

    def test_repo_security_scanner_integration(self):
        random_severity = self.severities[uuid.uuid4().int % len(self.severities)]
        
        payload = {
            "scan_uuid": self.scan_uuid,
            "path": self.test_dir.name,
            "severity": random_severity
        }

        result = repo_security_scanner(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("scan_uuid"), self.scan_uuid)
        self.assertEqual(result.get("path"), self.test_dir.name)
        
        vulnerabilities = result.get("vulnerabilities")
        self.assertIsInstance(vulnerabilities, list)

        if vulnerability_analyzer:
            expected_vuln = vulnerability_analyzer(target_path=self.test_dir.name, threshold=random_severity)
            if isinstance(expected_vuln, dict):
                self.assertIn(expected_vuln, vulnerabilities)


if __name__ == "__main__":
    unittest.main()