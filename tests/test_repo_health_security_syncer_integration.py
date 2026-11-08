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
        self.random_repo_id = str(uuid.uuid4())
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.random_repo_id,
            target_directory=self.test_dir
        )

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_synchronization_with_payload_and_file_persistence(self):
        random_sync_id = str(uuid.uuid4())
        random_health_score = round(random.uniform(50.0, 100.0), 2)
        random_vulnerabilities_count = random.randint(0, 10)
        random_security_score = round(random.uniform(0.0, 100.0), 2)
        
        payload = {
            "sync_id": random_sync_id,
            "health_score": random_health_score,
            "vulnerabilities": random_vulnerabilities_count,
            "security_score": random_security_score
        }

        result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], random_sync_id)
        self.assertEqual(result["health_data"]["health_score"], random_health_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], random_vulnerabilities_count)
        self.assertEqual(result["security_data"]["security_score"], random_security_score)

        expected_file_name = f"audit_{random_sync_id}.json"
        expected_file_path = os.path.join(self.test_dir, expected_file_name)
        
        self.assertTrue(os.path.exists(expected_file_path), "Audit JSON file was not created on disk.")

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)

        self.assertEqual(file_content["correlation_id"], random_sync_id)
        self.assertEqual(file_content["health_metrics"]["health_score"], random_health_score)
        self.assertEqual(file_content["security_metrics"]["vulnerabilities"], random_vulnerabilities_count)

    def test_synchronization_token_validation(self):
        random_token = str(uuid.uuid4())
        wrong_token = str(uuid.uuid4())
        
        os.environ["REPO_SYNC_TOKEN"] = random_token
        
        try:
            payload_invalid = {
                "sync_id": str(uuid.uuid4()),
                "token": wrong_token,
                "health_score": random.randint(1, 100)
            }
            result_invalid = self.syncer.synchronize(metric_payload=payload_invalid)
            self.assertFalse(result_invalid["success"])

            payload_valid = {
                "sync_id": str(uuid.uuid4()),
                "token": random_token,
                "health_score": random.randint(1, 100)
            }
            result_valid = self.syncer.synchronize(metric_payload=payload_valid)
            self.assertTrue(result_valid["success"])
        finally:
            if "REPO_SYNC_TOKEN" in os.environ:
                del os.environ["REPO_SYNC_TOKEN"]

if __name__ == "__main__":
    unittest.main()