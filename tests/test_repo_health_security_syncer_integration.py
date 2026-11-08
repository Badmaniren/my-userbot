import unittest
import os
import uuid
import random
import tempfile
import json
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_id = str(uuid.uuid4())
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            target_directory=self.test_dir
        )

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)
        if "REPO_SYNC_TOKEN" in os.environ:
            del os.environ["REPO_SYNC_TOKEN"]

    def test_synchronize_payload_integration(self):
        sync_id = uuid.uuid4().hex
        health_score = round(random.uniform(50.0, 100.0), 2)
        security_score = round(random.uniform(50.0, 100.0), 2)
        vulnerabilities_count = random.randint(0, 5)

        metric_payload = {
            "sync_id": sync_id,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": [{"id": str(uuid.uuid4())} for _ in range(vulnerabilities_count)]
        }

        result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)
        
        expected_file = os.path.join(self.test_dir, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file))

        with open(expected_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data.get("correlation_id"), sync_id)
        self.assertEqual(file_data.get("health_metrics", {}).get("health_score"), health_score)
        self.assertEqual(file_data.get("security_metrics", {}).get("security_score"), security_score)
        self.assertEqual(len(file_data.get("security_metrics", {}).get("vulnerabilities")), vulnerabilities_count)

    def test_synchronize_with_token_validation(self):
        env_token = uuid.uuid4().hex
        os.environ["REPO_SYNC_TOKEN"] = env_token

        sync_id = uuid.uuid4().hex
        wrong_token = uuid.uuid4().hex

        payload_fail = {
            "sync_id": sync_id,
            "token": wrong_token,
            "health_score": random.randint(1, 100),
            "security_score": random.randint(1, 100),
            "vulnerabilities": []
        }

        result_fail = self.syncer.synchronize(metric_payload=payload_fail)
        self.assertFalse(result_fail.get("success"))
        self.assertEqual(result_fail.get("synced_id"), sync_id)

        payload_success = {
            "sync_id": sync_id,
            "token": env_token,
            "health_score": random.randint(1, 100),
            "security_score": random.randint(1, 100),
            "vulnerabilities": []
        }

        result_success = self.syncer.synchronize(metric_payload=payload_success)
        self.assertTrue(result_success.get("success"))
        self.assertEqual(result_success.get("synced_id"), sync_id)
        self.assertEqual(result_success.get("health_data").get("token"), env_token)
        self.assertEqual(result_success.get("security_data").get("token"), env_token)

if __name__ == "__main__":
    unittest.main()