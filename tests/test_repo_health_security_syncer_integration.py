import unittest
import os
import uuid
import random
import json
import tempfile
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_id = str(uuid.uuid4())
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            target_directory=self.test_dir
        )

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_synchronize_payload_integration(self):
        sync_id = str(uuid.uuid4())
        health_score = round(random.uniform(50.0, 100.0), 2)
        security_score = round(random.uniform(50.0, 100.0), 2)
        vuln_count = random.randint(0, 5)
        vulnerabilities = [f"CVE-{random.randint(1000, 9999)}" for _ in range(vuln_count)]

        payload = {
            "sync_id": sync_id,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["security_data"]["security_score"], security_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)

        expected_file_name = f"audit_{sync_id}.json"
        expected_file_path = os.path.join(self.test_dir, expected_file_name)
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            audit_data = json.load(f)

        self.assertEqual(audit_data["correlation_id"], sync_id)
        self.assertEqual(audit_data["health_metrics"]["health_score"], health_score)
        self.assertEqual(audit_data["security_metrics"]["vulnerabilities"], vulnerabilities)

    def test_synchronize_token_validation(self):
        sync_id = str(uuid.uuid4())
        expected_token = str(uuid.uuid4())
        os.environ["REPO_SYNC_TOKEN"] = expected_token

        try:
            payload_invalid = {
                "sync_id": sync_id,
                "token": "wrong_token",
                "health_score": 90.0
            }
            result_invalid = self.syncer.synchronize(metric_payload=payload_invalid)
            self.assertFalse(result_invalid["success"])

            payload_valid = {
                "sync_id": sync_id,
                "token": expected_token,
                "health_score": 95.0
            }
            result_valid = self.syncer.synchronize(metric_payload=payload_valid)
            self.assertTrue(result_valid["success"])
        finally:
            if "REPO_SYNC_TOKEN" in os.environ:
                del os.environ["REPO_SYNC_TOKEN"]

if __name__ == "__main__":
    unittest.main()