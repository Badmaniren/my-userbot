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
            health_url="http://localhost:1",
            security_url="http://localhost:1",
            target_directory=self.test_dir
        )

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_synchronize_payload_integration_flow(self):
        random_sync_id = str(uuid.uuid4())
        random_health_score = round(random.uniform(0.0, 100.0), 2)
        random_security_score = round(random.uniform(0.0, 100.0), 2)
        random_vulnerabilities_count = random.randint(0, 10)
        
        payload = {
            "sync_id": random_sync_id,
            "health_score": random_health_score,
            "security_score": random_security_score,
            "vulnerabilities": {"critical": random_vulnerabilities_count}
        }

        result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), random_sync_id)
        self.assertEqual(result.get("health_data").get("health_score"), random_health_score)
        self.assertEqual(result.get("security_data").get("security_score"), random_security_score)

        expected_file_name = f"audit_{random_sync_id}.json"
        expected_file_path = os.path.join(self.test_dir, expected_file_name)
        
        self.assertTrue(os.path.exists(expected_file_path), "Audit file was not created on disk.")

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)

        self.assertEqual(file_content.get("correlation_id"), random_sync_id)
        self.assertEqual(file_content.get("health_metrics").get("health_score"), random_health_score)
        self.assertEqual(file_content.get("security_metrics").get("vulnerabilities").get("critical"), random_vulnerabilities_count)

if __name__ == "__main__":
    unittest.main()