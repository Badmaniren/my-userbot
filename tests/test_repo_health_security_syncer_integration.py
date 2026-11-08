import os
import uuid
import random
import json
import unittest
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncerIntegration(unittest.TestCase):
    def setUp(self):
        self.target_directory = f"./test_audit_dir_{uuid.uuid4()}"
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=str(uuid.uuid4()),
            target_directory=self.target_directory
        )

    def tearDown(self):
        if os.path.exists(self.target_directory):
            for file_name in os.listdir(self.target_directory):
                file_path = os.path.join(self.target_directory, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.target_directory)

    def test_synchronize_payload_integration(self):
        random_sync_id = str(uuid.uuid4())
        random_health_score = round(random.uniform(50.0, 100.0), 2)
        random_security_score = round(random.uniform(10.0, 99.9), 2)
        random_vulnerabilities_count = random.randint(0, 5)

        payload = {
            "sync_id": random_sync_id,
            "health_score": random_health_score,
            "security_score": random_security_score,
            "vulnerabilities": ["CVE-2023-" + str(random.randint(1000, 9999)) for _ in range(random_vulnerabilities_count)]
        }

        result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], random_sync_id)
        self.assertEqual(result["health_data"]["health_score"], random_health_score)
        self.assertEqual(result["security_data"]["security_score"], random_security_score)
        self.assertEqual(len(result["security_data"]["vulnerabilities"]), random_vulnerabilities_count)

        expected_file_name = f"audit_{random_sync_id}.json"
        expected_file_path = os.path.join(self.target_directory, expected_file_name)
        
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            audit_data = json.load(f)

        self.assertEqual(audit_data["correlation_id"], random_sync_id)
        self.assertEqual(audit_data["health_metrics"]["health_score"], random_health_score)
        self.assertEqual(audit_data["security_metrics"]["vulnerabilities"], payload["vulnerabilities"])

if __name__ == "__main__":
    unittest.main()