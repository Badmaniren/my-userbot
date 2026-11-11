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
        self.sync_id = uuid.uuid4().hex
        self.health_score = random.randint(50, 100)
        self.security_score = random.randint(50, 100)
        self.vulnerabilities_count = random.randint(0, 5)
        self.vulnerabilities = [f"CVE-2023-{random.randint(1000, 9999)}" for _ in range(self.vulnerabilities_count)]
        self.token = uuid.uuid4().hex

    def tearDown(self):
        if os.path.exists(self.test_dir):
            for root, dirs, files in os.walk(self.test_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.test_dir)

    def test_synchronize_with_payload_and_file_audit(self):
        os.environ["REPO_SYNC_TOKEN"] = self.token
        
        syncer = RepoHealthSecuritySyncer(
            repo_id=uuid.uuid4().hex,
            target_directory=self.test_dir
        )

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
        
        expected_file = os.path.join(self.test_dir, f"audit_{self.sync_id}.json")
        self.assertTrue(os.path.exists(expected_file))

        with open(expected_file, "r", encoding="utf-8") as f:
            audit_data = json.load(f)

        self.assertEqual(audit_data.get("correlation_id"), self.sync_id)
        self.assertEqual(audit_data.get("health_metrics", {}).get("health_score"), self.health_score)
        self.assertEqual(audit_data.get("security_metrics", {}).get("security_score"), self.security_score)
        self.assertEqual(audit_data.get("security_metrics", {}).get("vulnerabilities"), self.vulnerabilities)

        if "REPO_SYNC_TOKEN" in os.environ:
            del os.environ["REPO_SYNC_TOKEN"]

    def test_synchronize_token_mismatch(self):
        correct_token = uuid.uuid4().hex
        wrong_token = uuid.uuid4().hex
        os.environ["REPO_SYNC_TOKEN"] = correct_token

        syncer = RepoHealthSecuritySyncer()
        payload = {
            "sync_id": self.sync_id,
            "token": wrong_token,
            "health_score": self.health_score
        }

        result = syncer.synchronize(metric_payload=payload)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("synced_id"), self.sync_id)

        if "REPO_SYNC_TOKEN" in os.environ:
            del os.environ["REPO_SYNC_TOKEN"]

if __name__ == "__main__":
    unittest.main()