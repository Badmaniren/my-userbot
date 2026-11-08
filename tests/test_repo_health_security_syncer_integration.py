import unittest
import os
import uuid
import random
import json
import tempfile
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncerIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_id = str(uuid.uuid4())
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            target_directory=self.temp_dir.name
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_synchronize_with_payload_and_file_creation(self):
        random_sync_id = str(uuid.uuid4())
        random_health_score = round(random.uniform(0.0, 100.0), 2)
        random_security_score = round(random.uniform(0.0, 100.0), 2)
        random_vulnerability_count = random.randint(0, 10)
        
        payload = {
            "sync_id": random_sync_id,
            "health_score": random_health_score,
            "security_score": random_security_score,
            "vulnerabilities": [{"id": f"CVE-{random.randint(1000, 9999)}"} for _ in range(random_vulnerability_count)]
        }

        result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], random_sync_id)
        self.assertEqual(result["health_data"]["health_score"], random_health_score)
        self.assertEqual(result["security_data"]["security_score"], random_security_score)
        self.assertEqual(len(result["security_data"]["vulnerabilities"]), random_vulnerability_count)

        expected_file_name = f"audit_{random_sync_id}.json"
        expected_file_path = os.path.join(self.temp_dir.name, expected_file_name)
        
        self.assertTrue(os.path.exists(expected_file_path), f"Audit file {expected_file_path} was not created.")

        with open(expected_file_path, "r", encoding="utf-8") as f:
            audit_data = json.load(f)

        self.assertEqual(audit_data["correlation_id"], random_sync_id)
        self.assertEqual(audit_data["health_metrics"]["health_score"], random_health_score)
        self.assertEqual(len(audit_data["security_metrics"]["vulnerabilities"]), random_vulnerability_count)

    def test_synchronize_token_validation_failure(self):
        random_sync_id = str(uuid.uuid4())
        correct_token = str(uuid.uuid4())
        wrong_token = str(uuid.uuid4())

        os.environ["REPO_SYNC_TOKEN"] = correct_token

        payload = {
            "sync_id": random_sync_id,
            "token": wrong_token,
            "health_score": random.randint(50, 100)
        }

        try:
            result = self.syncer.synchronize(metric_payload=payload)
            self.assertFalse(result["success"])
            self.assertEqual(result["synced_id"], random_sync_id)
        finally:
            if "REPO_SYNC_TOKEN" in os.environ:
                del os.environ["REPO_SYNC_TOKEN"]

    def test_synchronize_token_validation_success(self):
        random_sync_id = str(uuid.uuid4())
        shared_token = str(uuid.uuid4())

        os.environ["REPO_SYNC_TOKEN"] = shared_token

        payload = {
            "sync_id": random_sync_id,
            "token": shared_token,
            "health_score": random.randint(50, 100)
        }

        try:
            result = self.syncer.synchronize(metric_payload=payload)
            self.assertTrue(result["success"])
            self.assertEqual(result["synced_id"], random_sync_id)
        finally:
            if "REPO_SYNC_TOKEN" in os.environ:
                del os.environ["REPO_SYNC_TOKEN"]

if __name__ == "__main__":
    unittest.main()