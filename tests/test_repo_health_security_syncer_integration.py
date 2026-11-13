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
        self.sync_id = uuid.uuid4().hex
        self.health_score = round(random.uniform(50.0, 100.0), 2)
        self.security_score = round(random.uniform(50.0, 100.0), 2)
        self.vulnerabilities_count = random.randint(0, 10)

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_synchronize_with_payload_and_filesystem(self):
        syncer = RepoHealthSecuritySyncer(
            repo_id=str(uuid.uuid4()),
            target_directory=self.test_dir
        )
        
        payload = {
            "sync_id": self.sync_id,
            "health_score": self.health_score,
            "security_score": self.security_score,
            "vulnerabilities": self.vulnerabilities_count
        }

        result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), self.sync_id)
        
        expected_file = os.path.join(self.test_dir, f"audit_{self.sync_id}.json")
        self.assertTrue(os.path.exists(expected_file))

        with open(expected_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data.get("correlation_id"), self.sync_id)
        self.assertEqual(file_data.get("health_metrics", {}).get("health_score"), self.health_score)
        self.assertEqual(file_data.get("security_metrics", {}).get("security_score"), self.security_score)
        self.assertEqual(file_data.get("security_metrics", {}).get("vulnerabilities"), self.vulnerabilities_count)

    def test_synchronize_token_validation_failure(self):
        env_token_value = uuid.uuid4().hex
        os.environ["REPO_SYNC_TOKEN"] =