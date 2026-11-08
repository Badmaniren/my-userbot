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
        self.sync_id = str(uuid.uuid4())
        self.token = str(uuid.uuid4())
        os.environ["REPO_SYNC_TOKEN"] = self.token
        
        self.health_score = random.randint(50, 100)
        self.security_score = random.randint(50, 100)
        self.vulnerabilities_count = random.randint(0, 5)
        self.vulnerabilities = [f"CVE-2023-{random.randint(1000, 9999)}" for _ in range(self.vulnerabilities_count)]

    def tearDown(self):
        if "REPO_SYNC_TOKEN" in os.environ:
            del os.environ["REPO_SYNC_TOKEN"]
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_synchronize_with_payload_and_file_persistence(self):
        syncer = RepoHealthSecuritySyncer(target_directory=self.test_dir)
        
        payload = {
            "sync_id": self.sync_id,
            "token": self.token,
            "health_score": self.health_score,
            "security_score": self.security_score,
            "vulnerabilities": self.vulnerabilities
        }

        result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), self.sync_id)
        self.assertEqual(result.get("health_data", {}).get("health_score"), self.health_score)
        self.assertEqual(result.get("security_data", {}).get("security_score"), self.security_score)
        self.assertEqual(result.get("security_data", {}).get("vulnerabilities"), self.vulnerabilities)

        expected_file_name = f"audit_{self.sync_id}.json"
        expected_file_path = os.path.join(self.test_dir, expected_file_name)
        
        self.assertTrue(os.path.exists(expected_file_path), "Audit file was not created on disk.")

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data.get("correlation_id"), self.sync_id)
        self.assertEqual(file_data.get("health_metrics", {}).get("health_score"), self.health_score)
        self.assertEqual(file_data.get("security_metrics", {}).get("vulnerabilities"), self.vulnerabilities)

    def test_synchronize_token_mismatch(self):
        syncer = RepoHealthSecuritySyncer(target_directory=self.test_dir)
        
        wrong_token = str(uuid.uuid4())
        payload = {
            "sync_id": self.sync_id,
            "token": wrong_token,
            "health_score": self.health_score,
            "security_score": self.security_score,
            "vulnerabilities": self.vulnerabilities
        }

        result = syncer.synchronize(metric_payload=payload)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("synced_id"), self.sync_id)

if __name__ == "__main__":
    unittest.main()