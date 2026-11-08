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

    def test_synchronize_payload_integration(self):
        random_sync_id = str(uuid.uuid4())
        random_health_score = round(random.uniform(1.0, 100.0), 2)
        random_vulnerabilities_count = random.randint(0, 10)
        
        payload = {
            "sync_id": random_sync_id,
            "health_score": random_health_score,
            "vulnerabilities": random_vulnerabilities_count,
            "security_score": round(random.uniform(1.0, 100.0), 2)
        }

        result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], random_sync_id)
        self.assertEqual(result["health_data"]["health_score"], random_health_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], random_vulnerabilities_count)

        expected_file_name = f"audit_{random_sync_id}.json"
        expected_file_path = os.path.join(self.test_dir.name, expected_file_name)
        
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            audit_data = json.load(f)

        self.assertEqual(audit_data["correlation_id"], random_sync_id)
        self.assertEqual(audit_data["health_metrics"]["health_score"], random_health_score)
        self.assertEqual(audit_data["security_metrics"]["vulnerabilities"], random_vulnerabilities_count)

    def test_synchronize_payload_with_token_validation(self):
        random_sync_id = str(uuid.uuid4())
        expected_token = str(uuid.uuid4())
        os.environ["REPO_SYNC_TOKEN"] = expected_token

        try:
            payload_valid = {
                "sync_id": random_sync_id,
                "token": expected_token,
                "health_score": 95.5,
                "vulnerabilities": 0
            }
            result_valid = self.syncer.synchronize(metric_payload=payload_valid)
            self.assertTrue(result_valid["success"])

            payload_invalid = {
                "sync_id": str(uuid.uuid4()),
                "token": "invalid_token_string",
                "health_score": 50.0,
                "vulnerabilities": 5
            }
            result_invalid = self.syncer.synchronize(metric_payload=payload_invalid)
            self.assertFalse(result_invalid["success"])
        finally:
            if "REPO_SYNC_TOKEN" in os.environ:
                del os.environ["REPO_SYNC_TOKEN"]

if __name__ == "__main__":
    unittest.main()