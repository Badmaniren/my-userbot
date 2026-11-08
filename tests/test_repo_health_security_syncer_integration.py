import unittest
import os
import uuid
import json
import random
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncerIntegration(unittest.TestCase):
    def setUp(self):
        self.target_dir = f"./test_audit_dir_{uuid.uuid4().hex}"
        self.syncer = RepoHealthSecuritySyncer(target_directory=self.target_dir)

    def tearDown(self):
        if os.path.exists(self.target_dir):
            for filename in os.listdir(self.target_dir):
                file_path = os.path.join(self.target_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.target_dir)

    def test_synchronize_payload_integration_flow(self):
        sync_id = str(uuid.uuid4())
        health_score = round(random.uniform(50.0, 100.0), 2)
        security_score = round(random.uniform(50.0, 100.0), 2)
        vulnerabilities_count = random.randint(0, 10)
        
        payload = {
            "sync_id": sync_id,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": {"critical": vulnerabilities_count}
        }

        result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["security_data"]["security_score"], security_score)

        expected_file_path = os.path.join(self.target_dir, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)

        self.assertEqual(file_content["correlation_id"], sync_id)
        self.assertEqual(file_content["health_metrics"]["health_score"], health_score)
        self.assertEqual(file_content["security_metrics"]["security_score"], security_score)
        self.assertEqual(file_content["security_metrics"]["vulnerabilities"]["critical"], vulnerabilities_count)

if __name__ == "__main__":
    unittest.main()