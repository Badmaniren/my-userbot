import os
import uuid
import random
import json
import unittest
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncerIntegration(unittest.TestCase):
    def setUp(self):
        self.sync_id = str(uuid.uuid4())
        self.target_dir = f"test_audit_dir_{uuid.uuid4()}"
        self.health_score = round(random.uniform(50.0, 100.0), 2)
        self.security_score = round(random.uniform(50.0, 100.0), 2)
        self.vulnerabilities_count = random.randint(0, 10)
        self.token_val = f"token_{uuid.uuid4()}"

    def tearDown(self):
        if os.path.exists(self.target_dir):
            for filename in os.listdir(self.target_dir):
                file_path = os.path.join(self.target_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.target_dir)

    def test_synchronize_with_payload_creates_audit_file(self):
        os.environ["REPO_SYNC_TOKEN"] = self.token_val
        
        syncer = RepoHealthSecuritySyncer(target_directory=self.target_dir)
        payload = {
            "sync_id": self.sync_id,
            "token": self.token_val,
            "health_score": self.health_score,
            "security_score": self.security_score,
            "vulnerabilities": self.vulnerabilities_count
        }

        result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), self.sync_id)
        
        expected_file_path = os.path.join(self.target_dir, f"audit_{self.sync_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data.get("correlation_id"), self.sync_id)
        self.assertEqual(file_data.get("health_metrics", {}).get("health_score"), self.health_score)
        self.assertEqual(file_data.get("security_metrics", {}).get("security_score"), self.security_score)
        self.assertEqual(file_data.get("security_metrics", {}).get("vulnerabilities"), self.vulnerabilities_count)

    def test_synchronize_invalid_token_fails(self):
        os.environ["REPO_SYNC_TOKEN"] = self.token_val
        wrong_token = f"wrong_{uuid.uuid4()}"

        syncer = RepoHealthSecuritySyncer(target_directory=self.target_dir)
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
        
        expected_file_path = os.path.join(self.target_dir, f"audit_{self.sync_id}.json")
        self.assertFalse(os.path.exists(expected_file_path))

if __name__ == "__main__":
    unittest.main()