import unittest
import os
import tempfile
import uuid
import random
import json
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.sync_id = str(uuid.uuid4())
        self.token = str(uuid.uuid4())
        os.environ["REPO_SYNC_TOKEN"] = self.token
        
        self.health_score = round(random.uniform(50.0, 100.0), 2)
        self.security_score = round(random.uniform(0.0, 100.0), 2)
        self.vulnerabilities_count = random.randint(0, 10)

    def tearDown(self):
        self.test_dir.cleanup()
        if "REPO_SYNC_TOKEN" in os.environ:
            del os.environ["REPO_SYNC_TOKEN"]

    def test_synchronize_with_payload_and_file_generation(self):
        syncer = RepoHealthSecuritySyncer(target_directory=self.test_dir.name)
        
        payload = {
            "sync_id": self.sync_id,
            "token": self.token,
            "health_score": self.health_score,
            "vulnerabilities": self.vulnerabilities_count,
            "security_score": self.security_score
        }

        result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], self.sync_id)
        self.assertEqual(result["health_data"]["health_score"], self.health_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], self.vulnerabilities_count)
        self.assertEqual(result["security_data"]["security_score"], self.security_score)

        expected_file_name = f"audit_{self.sync_id}.json"
        expected_file_path = os.path.join(self.test_dir.name, expected_file_name)
        
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            audit_data = json.load(f)

        self.assertEqual(audit_data["correlation_id"], self.sync_id)
        self.assertEqual(audit_data["health_metrics"]["health_score"], self.health_score)
        self.assertEqual(audit_data["security_metrics"]["vulnerabilities"], self.vulnerabilities_count)

    def test_synchronize_invalid_token(self):
        syncer = RepoHealthSecuritySyncer(target_directory=self.test_dir.name)
        
        wrong_token = str(uuid.uuid4())
        payload = {
            "sync_id": self.sync_id,
            "token": wrong_token,
            "health_score": self.health_score,
            "vulnerabilities": self.vulnerabilities_count,
            "security_score": self.security_score
        }

        result = syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], self.sync_id)

if __name__ == "__main__":
    unittest.main()