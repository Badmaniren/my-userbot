import unittest
import os
import uuid
import random
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

    def test_synchronize_payload_success_and_file_audit(self):
        sync_id = str(uuid.uuid4())
        token_val = str(uuid.uuid4())
        health_score = round(random.uniform(50.0, 100.0), 2)
        vulnerabilities_count = random.randint(0, 5)
        security_score = round(random.uniform(10.0, 100.0), 2)

        os.environ["REPO_SYNC_TOKEN"] = token_val

        payload = {
            "sync_id": sync_id,
            "token": token_val,
            "health_score": health_score,
            "vulnerabilities": vulnerabilities_count,
            "security_score": security_score
        }

        result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)
        self.assertEqual(result.get("health_data", {}).get("health_score"), health_score)
        self.assertEqual(result.get("security_data", {}).get("vulnerabilities"), vulnerabilities_count)
        self.assertEqual(result.get("security_data", {}).get("security_score"), security_score)

        expected_file_name = f"audit_{sync_id}.json"
        expected_file_path = os.path.join(self.test_dir.name, expected_file_name)
        self.assertTrue(os.path.exists(expected_file_path))

    def test_synchronize_payload_invalid_token(self):
        sync_id = str(uuid.uuid4())
        os.environ["REPO_SYNC_TOKEN"] = "correct_token_value"
        
        payload = {
            "sync_id": sync_id,
            "token": "wrong_token_value",
            "health_score": random.randint(1, 100),
            "vulnerabilities": 0
        }

        result = self.syncer.synchronize(metric_payload=payload)
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)

    def test_synchronize_network_failure(self):
        invalid_syncer = RepoHealthSecuritySyncer(
            repo_id=str(uuid.uuid4()),
            health_url="http://localhost:1",
            security_url="http://localhost:1"
        )
        result = invalid_syncer.synchronize()
        self.assertFalse(result.get("success"))
        self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main()