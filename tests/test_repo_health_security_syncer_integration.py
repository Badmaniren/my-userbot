import unittest
import os
import uuid
import random
import tempfile
import json
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

    def test_synchronize_integration_with_real_filesystem_and_random_payload(self):
        sync_id = str(uuid.uuid4())
        health_score = round(random.uniform(50.0, 100.0), 2)
        security_score = round(random.uniform(50.0, 100.0), 2)
        vulnerabilities_count = random.randint(0, 10)
        
        payload = {
            "sync_id": sync_id,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities_count
        }

        os.environ.pop("REPO_SYNC_TOKEN", None)

        result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)
        
        expected_file_name = f"audit_{sync_id}.json"
        expected_file_path = os.path.join(self.test_dir.name, expected_file_name)
        
        self.assertTrue(os.path.exists(expected_file_path))
        
        with open(expected_file_path, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)

        self.assertEqual(persisted_data.get("correlation_id"), sync_id)
        self.assertEqual(persisted_data.get("health_metrics", {}).get("health_score"), health_score)
        self.assertEqual(persisted_data.get("security_metrics", {}).get("security_score"), security_score)
        self.assertEqual(persisted_data.get("security_metrics", {}).get("vulnerabilities"), vulnerabilities_count)

    def test_synchronize_with_token_validation_failure(self):
        sync_id = str(uuid.uuid4())
        random_token = str(uuid.uuid4())
        wrong_token = str(uuid.uuid4())

        os.environ["REPO_SYNC_TOKEN"] = random_token

        payload = {
            "sync_id": sync_id,
            "token": wrong_token,
            "health_score": random.randint(1, 100)
        }

        result = self.syncer.synchronize(metric_payload=payload)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)
        
        expected_file_path = os.path.join(self.test_dir.name, f"audit_{sync_id}.json")
        self.assertFalse(os.path.exists(expected_file_path))

        os.environ.pop("REPO_SYNC_TOKEN", None)

if __name__ == "__main__":
    unittest.main()