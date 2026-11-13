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
        self.rand_sync_id = uuid.uuid4().hex
        self.rand_health_score = round(random.uniform(50.0, 100.0), 2)
        self.rand_security_score = round(random.uniform(50.0, 100.0), 2)
        self.rand_vulnerabilities = random.randint(0, 10)
        self.rand_token = uuid.uuid4().hex

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
        syncer = RepoHealthSecuritySyncer(target_directory=self.test_dir)
        payload = {
            "sync_id": self.rand_sync_id,
            "health_score": self.rand_health_score,
            "security_score": self.rand_security_score,
            "vulnerabilities": self.rand_vulnerabilities
        }

        result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), self.rand_sync_id)
        
        expected_file = os.path.join(self.test_dir, f"audit_{self.rand_sync_id}.json")
        self.assertTrue(os.path.exists(expected_file))

        with open(expected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data.get("correlation_id"), self.rand_sync_id)
            self.assertEqual(data.get("health_metrics", {}).get("health_score"), self.rand_health_score)
            self.assertEqual(data.get("security_metrics", {}).get("security_score"), self.rand_security_score)
            self.assertEqual(data.get("security_metrics", {}).get("vulnerabilities"), self.rand_vulnerabilities)

    def test_synchronize_token_unauthorized_integration(self):
        os.environ["REPO_SYNC_TOKEN"] = self.rand_token
        wrong_token = uuid.uuid4().hex

        syncer = RepoHealthSecuritySyncer(target_directory=self.test_dir)
        payload = {
            "sync_id": self.rand_sync_id,
            "token": wrong_token,
            "health_score": self.rand_health_score
        }

        result = syncer.synchronize(metric_payload=payload)

        self.assertFalse(result.get("success