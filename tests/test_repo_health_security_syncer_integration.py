import unittest
import os
import uuid
import random
import json
import tempfile
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_id = str(uuid.uuid4())
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            target_directory=self.test_dir.name
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_synchronize_with_payload_creates_audit_file(self):
        random_sync_id = str(uuid.uuid4())
        random_health_score = round(random.uniform(0.0, 100.0), 2)
        random_vuln_count = random.randint(0, 15)
        
        payload = {
            "sync_id": random_sync_id,
            "health_score": random_health_score,
            "vulnerabilities": random_vuln_count
        }

        result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], random_sync_id)
        self.assertEqual(result["health_data"]["health_score"], random_health_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], random_vuln_count)

        expected_file_name = f"audit_{random_sync_id}.json"
        expected_file_path = os.path.join(self.test_dir.name, expected_file_name)
        
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data["correlation_id"], random_sync_id)
        self.assertEqual(file_data["health_metrics"]["health_score"], random_health_score)
        self.assertEqual(file_data["security_metrics"]["vulnerabilities"], random_vuln_count)

    def test_synchronize_token_validation_failure(self):
        random_sync_id = str(uuid.uuid4())
        correct_token = str(uuid.uuid4())
        wrong_token = str(uuid.uuid4())

        os.environ["REPO_SYNC_TOKEN"] = correct_token

        payload = {
            "sync_id": random_sync_id,
            "token": wrong_token,
            "health_score": random.randint(50, 100),
            "vulnerabilities": 0
        }

        try:
            result = self.syncer.synchronize(metric_payload=payload)
            self.assertFalse(result["success"])
            self.assertEqual(result["synced_id"], random_sync_id)
        finally:
            if "REPO_SYNC_TOKEN" in os.environ:
                del os.environ["REPO_SYNC_TOKEN"]

if __name__ == "__main__":
    unittest.main()