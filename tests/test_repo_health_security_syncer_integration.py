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
        self.rand_health_score = round(random.uniform(50.0, 100.0), 2)
        self.rand_security_score = round(random.uniform(40.0, 99.9), 2)
        self.rand_vulns_count = random.randint(0, 15)
        self.rand_sync_id = uuid.uuid4().hex

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_synchronize_payload_flow_and_file_generation(self):
        syncer = RepoHealthSecuritySyncer(
            repo_id=uuid.uuid4().hex,
            target_directory=self.test_dir
        )

        payload = {
            "sync_id": self.rand_sync_id,
            "health_score": self.rand_health_score,
            "security_score": self.rand_security_score,
            "vulnerabilities": self.rand_vulns_count
        }

        result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), self.rand_sync_id)
        
        self.assertIn("health_data", result)
        self.assertIn("security_data", result)
        self.assertEqual(result["health_data"].get("health_score"), self.rand_health_score)
        self.assertEqual(result["security_data"].get("security_score"), self.rand_security_score)
        self.assertEqual(result["security_data"].get("vulnerabilities"), self.rand_vulns_count)

        expected_file_path = os.path.join(self.test_dir, f"audit_{self.rand_sync_id}.json")
        self.assertTrue(os.path.exists(expected_file_path), "Интеграционный файл аудита не был создан на диске.")

        with open(expected_file_path, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)

        self.assertEqual(persisted_data.get("correlation_id"), self.rand_sync_id)
        self.assertEqual(persisted_data["health_metrics"].get("health_score"), self.rand_health_score)
        self.assertEqual(persisted_data["security_metrics"].get("security_score"), self.rand_security_score)
        self.assertEqual(persisted_data["security_metrics"].get("vulnerabilities"), self.rand_vulns_count)

    def test_synchronize_token_validation_failure(self):
        rand_env_token = uuid.uuid4().hex
        rand_bad_token = uuid.uuid4().hex

        os.environ["REPO_SYNC_TOKEN"] = rand_env_token
        try:
            syncer = RepoHealthSecuritySyncer()
            payload = {
                "sync_id": self.rand_sync_id,
                "token": rand_bad_token,
                "health_score": self.rand_health_score
            }
            result = syncer.synchronize(metric_payload=payload)
            self.assertFalse(result.get("success"))
            self.assertEqual(result.get("synced_id"), self.rand_sync_id)
        finally:
            if "REPO_SYNC_TOKEN" in os.environ:
                del os.environ["REPO_SYNC_TOKEN"]

if __name__ == "__main__":
    unittest.main()