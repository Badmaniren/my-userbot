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

    def test_synchronize_payload_integration_with_real_filesystem(self):
        random_sync_id = str(uuid.uuid4())
        random_health = round(random.uniform(50.0, 100.0), 2)
        random_vulns_count = random.randint(0, 5)
        random_security_score = round(random.uniform(0.0, 100.0), 2)
        
        payload = {
            "sync_id": random_sync_id,
            "health_score": random_health,
            "vulnerabilities": random_vulns_count,
            "security_score": random_security_score
        }

        result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], random_sync_id)
        self.assertEqual(result["health_data"]["health_score"], random_health)
        self.assertEqual(result["security_data"]["vulnerabilities"], random_vulns_count)
        self.assertEqual(result["security_data"]["security_score"], random_security_score)

        expected_file_name = f"audit_{random_sync_id}.json"
        expected_file_path = os.path.join(self.test_dir.name, expected_file_name)
        
        self.assertTrue(os.path.exists(expected_file_path), "Audit file must be physically created on the disk.")

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)

        self.assertEqual(file_content["correlation_id"], random_sync_id)
        self.assertEqual(file_content["health_metrics"]["health_score"], random_health)
        self.assertEqual(file_content["security_metrics"]["vulnerabilities"], random_vulns_count)
        self.assertIn("audit_id", file_content)

    def test_synchronize_token_validation_integration(self):
        random_token = str(uuid.uuid4())
        wrong_token = str(uuid.uuid4())
        
        os.environ["REPO_SYNC_TOKEN"] = random_token
        
        try:
            payload_invalid = {
                "sync_id": str(uuid.uuid4()),
                "token": wrong_token,
                "health_score": random.randint(1, 100),
                "vulnerabilities": 0
            }
            result_invalid = self.syncer.synchronize(metric_payload=payload_invalid)
            self.assertFalse(result_invalid["success"], "Synchronization must fail with incorrect token.")

            payload_valid = {
                "sync_id": str(uuid.uuid4()),
                "token": random_token,
                "health_score": random.randint(1, 100),
                "vulnerabilities": 0
            }
            result_valid = self.syncer.synchronize(metric_payload=payload_valid)
            self.assertTrue(result_valid["success"], "Synchronization must succeed with matching token.")
        finally:
            if "REPO_SYNC_TOKEN" in os.environ:
                del os.environ["REPO_SYNC_TOKEN"]

if __name__ == "__main__":
    unittest.main()