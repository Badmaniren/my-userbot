import unittest
import os
import uuid
import tempfile
import json
import random
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_id = str(uuid.uuid4())
        self.sync_token = str(uuid.uuid4())
        os.environ["REPO_SYNC_TOKEN"] = self.sync_token

    def tearDown(self):
        if "REPO_SYNC_TOKEN" in os.environ:
            del os.environ["REPO_SYNC_TOKEN"]
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_synchronize_payload_integration(self):
        random_sync_id = str(uuid.uuid4())
        random_health_score = round(random.uniform(50.0, 100.0), 2)
        random_vuln_count = random.randint(0, 10)
        random_security_score = round(random.uniform(0.0, 100.0), 2)

        payload = {
            "sync_id": random_sync_id,
            "token": self.sync_token,
            "health_score": random_health_score,
            "vulnerabilities": random_vuln_count,
            "security_score": random_security_score
        }

        syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            target_directory=self.test_dir
        )

        result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], random_sync_id)
        self.assertEqual(result["health_data"]["health_score"], random_health_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], random_vuln_count)
        self.assertEqual(result["security_data"]["security_score"], random_security_score)

        expected_file_name = f"audit_{random_sync_id}.json"
        expected_file_path = os.path.join(self.test_dir, expected_file_name)
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            audit_data = json.load(f)

        self.assertEqual(audit_data["correlation_id"], random_sync_id)
        self.assertEqual(audit_data["health_metrics"]["health_score"], random_health_score)
        self.assertEqual(audit_data["security_metrics"]["vulnerabilities"], random_vuln_count)

    def test_synchronize_payload_invalid_token(self):
        random_sync_id = str(uuid.uuid4())
        wrong_token = str(uuid.uuid4())

        payload = {
            "sync_id": random_sync_id,
            "token": wrong_token,
            "health_score": random.randint(0, 100),
            "vulnerabilities": random.randint(0, 5),
            "security_score": random.randint(0, 100)
        }

        syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            target_directory=self.test_dir
        )

        result = syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], random_sync_id)

if __name__ == "__main__":
    unittest.main()