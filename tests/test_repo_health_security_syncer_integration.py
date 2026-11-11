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

    def test_synchronize_with_generated_payload(self):
        sync_id = uuid.uuid4().hex
        health_score = round(random.uniform(50.0, 100.0), 2)
        security_score = round(random.uniform(0.0, 100.0), 2)
        vuln_count = random.randint(0, 5)
        vulnerabilities = [f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 9999)}" for _ in range(vuln_count)]

        metric_payload = {
            "sync_id": sync_id,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)
        
        expected_file = os.path.join(self.test_dir, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file))

        with open(expected_file, "r", encoding="utf-8") as f:
            audit_data = json.load(f)

        self.assertEqual(audit_data.get("correlation_id"), sync_id)
        self.assertEqual(audit_data.get("health_metrics", {}).get("health_score"), health_score)
        self.assertEqual(audit_data.get("security_metrics", {}).get("security_score"), security_score)
        self.assertEqual(audit_data.get("security_metrics", {}).get("vulnerabilities"), vulnerabilities)

    def test_synchronize_with_token_validation(self):
        sync_id = uuid.uuid4().hex
        valid_token = uuid.uuid4().hex
        os.environ["REPO_SYNC_TOKEN"] = valid_token

        try:
            metric_payload_invalid = {
                "sync_id": sync_id,
                "token": "wrong_token",
                "health_score": 90.0,
                "security_score": 85.0,
                "vulnerabilities": []
            }
            result_invalid = self.syncer.synchronize(metric_payload=metric_payload_invalid)
            self.assertFalse(result_invalid.get("success"))
            self.assertEqual(result_invalid.get("synced_id"), sync_id)

            metric_payload_valid = {
                "sync_id": sync_id,
                "token": valid_token,
                "health_score": 95.0,
                "security_score": 90.0,
                "vulnerabilities": []
            }
            result_valid = self.syncer.synchronize(metric_payload=metric_payload_valid)
            self.assertTrue(result_valid.get("success"))
            self.assertEqual(result_valid.get("synced_id"), sync_id)
        finally:
            if "REPO_SYNC_TOKEN" in os.environ:
                del os.environ["REPO_SYNC_TOKEN"]

if __name__ == "__main__":
    unittest.main()