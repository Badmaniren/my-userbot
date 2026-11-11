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

    def test_synchronize_integration_with_real_filesystem_and_payload(self):
        sync_id = uuid.uuid4().hex
        health_score = round(random.uniform(50.0, 100.0), 2)
        security_score = round(random.uniform(50.0, 100.0), 2)
        vulnerabilities_count = random.randint(0, 10)
        
        metric_payload = {
            "sync_id": sync_id,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities_count
        }

        result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)
        
        expected_file = os.path.join(self.test_dir, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file), "Audit file was not created on disk")

        with open(expected_file, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)

        self.assertEqual(persisted_data.get("correlation_id"), sync_id)
        self.assertEqual(persisted_data.get("health_metrics", {}).get("health_score"), health_score)
        self.assertEqual(persisted_data.get("security_metrics", {}).get("security_score"), security_score)
        self.assertEqual(persisted_data.get("security_metrics", {}).get("vulnerabilities"), vulnerabilities_count)

if __name__ == "__main__":
    unittest.main()