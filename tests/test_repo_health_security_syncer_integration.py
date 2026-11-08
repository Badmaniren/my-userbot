import unittest
import os
import uuid
import random
import tempfile
import json
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sync_id = uuid.uuid4().hex
        self.health_score = round(random.uniform(50.0, 100.0), 2)
        self.security_score = round(random.uniform(50.0, 100.0), 2)
        self.vulnerabilities_count = random.randint(0, 10)

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_synchronize_with_payload_and_disk_persistence(self):
        token = uuid.uuid4().hex
        os.environ["REPO_SYNC_TOKEN"] = token

        syncer = RepoHealthSecuritySyncer(
            repo_id=uuid.uuid4().hex,
            target_directory=self.test_dir
        )

        payload = {
            "sync_id": self.sync_id,
            "token": token,
            "health_score": self.health_score,
            "security_score": self.security_score,
            "vulnerabilities": self.vulnerabilities_count
        }

        result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), self.sync_id)

        expected_file_path = os.path.join(self.test_dir, f"audit_{self.sync_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)

        self.assertEqual(persisted_data.get("correlation_id"), self.sync_id)
        self.assertEqual(persisted_data.get("health_metrics", {}).get("health_score"), self.health_score)
        self.assertEqual(persisted_data.get("security_metrics", {}).get("security_score"), self.security_score)
        self.assertEqual(persisted_data.get("security_metrics", {}).get("vulnerabilities"), self.vulnerabilities_count)

        if "REPO_SYNC_TOKEN" in os.environ:
            del os.environ["REPO_SYNC_TOKEN"]

    def test_synchronize_unauthorized_token_rejection(self):
        env_token = uuid.uuid4().hex
        wrong_token = uuid.uuid4().hex
        os.environ["REPO_SYNC_TOKEN"] = env_token

        syncer = RepoHealthSecuritySyncer(target_directory=self.test_dir)
        payload = {
            "sync_id": self.sync_id,
            "token": wrong_token,
            "health_score": self.health_score,
            "security_score": self.security_score,
            "vulnerabilities": self.vulnerabilities_count
        }

        result = syncer.synchronize(metric_payload=payload)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("synced_id"), self.sync_id)
        
        expected_file_path = os.path.join(self.test_dir, f"audit_{self.sync_id}.json")
        self.assertFalse(os.path.exists(expected_file_path))

        if "REPO_SYNC_TOKEN" in os.environ:
            del os.environ["REPO_SYNC_TOKEN"]

if __name__ == "__main__":
    unittest.main()