import os
import json
import uuid
import random
import tempfile
import unittest

from skills.repo_health_security_syncer import RepoHealthSecuritySyncer
from skills.repo_security_gate_validator import RepoSecurityGateValidator


class TestRepoHealthSecuritySyncerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.target_directory = self.test_dir.name

    def tearDown(self):
        self.test_dir.cleanup()

    def test_synchronize_end_to_end_audit_creation_and_gate_validation(self):
        sync_id = uuid.uuid4().hex
        health_score = random.randint(60, 100)
        security_score = random.randint(70, 99)
        vulnerabilities = [
            f"CVE-{random.randint(2020, 2025)}-{random.randint(1000, 9999)}"
            for _ in range(random.randint(1, 4))
        ]

        payload = {
            "sync_id": sync_id,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        syncer = RepoHealthSecuritySyncer(target_directory=self.target_directory)
        result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)
        self.assertEqual(result.get("health_data", {}).get("health_score"), health_score)
        self.assertEqual(result.get("security_data", {}).get("security_score"), security_score)
        self.assertEqual(result.get("security_data", {}).get("vulnerabilities"), vulnerabilities)

        expected_audit_file = os.path.join(self.target_directory, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_audit_file))

        with open(expected_audit_file, "r", encoding="utf-8") as f:
            written_audit = json.load(f)

        self.assertEqual(written_audit.get("correlation_id"), sync_id)
        self.assertEqual(
            written_audit.get("health_metrics", {}).get("health_score"),
            health_score
        )
        self.assertEqual(
            written_audit.get("security_metrics", {}).get("security_score"),
            security_score
        )
        self.assertEqual(
            written_audit.get("security_metrics", {}).get("vulnerabilities"),
            vulnerabilities
        )

    def test_synchronize_with_token_protection_and_subfolder_creation(self):
        sub_folder = os.path.join(self.target_directory, f"sync_dir_{uuid.uuid4().hex[:8]}")
        auth_token = f"token_{uuid.uuid4().hex}"
        sync_id = uuid.uuid4().hex
        health_score = random.randint(40, 90)
        security_score = random.randint(50, 95)
        vulnerabilities = [f"VULN-{uuid.uuid4().hex[:6]}"]

        os.environ["REPO_SYNC_TOKEN"] = auth_token
        try:
            invalid_payload = {
                "sync_id": sync_id,
                "token": f"wrong_{auth_token}",
                "health_score": health_score,
                "security_score": security_score,
                "vulnerabilities": vulnerabilities
            }
            syncer = RepoHealthSecuritySyncer(target_directory=sub_folder)
            rejected_res = syncer.synchronize(metric_payload=invalid_payload)
            self.assertFalse(rejected_res.get("success"))
            self.assertEqual(rejected_res.get("synced_id"), sync_id)
            self.assertFalse(os.path.exists(sub_folder))

            valid_payload = {
                "sync_id": sync_id,
                "token": auth_token,
                "health_score": health_score,
                "security_score": security_score,
                "vulnerabilities": vulnerabilities
            }
            accepted_res = syncer.synchronize(metric_payload=valid_payload)
            self.assertTrue(accepted_res.get("success"))
            self.assertEqual(accepted_res.get("synced_id"), sync_id)
            self.assertEqual(accepted_res.get("health_data", {}).get("token"), auth_token)

            audit_file = os.path.join(sub_folder, f"audit_{sync_id}.json")
            self.assertTrue(os.path.exists(audit_file))

            with open(audit_file, "r", encoding="utf-8") as f:
                persisted = json.load(f)
            self.assertEqual(persisted["correlation_id"], sync_id)
        finally:
            os.environ.pop("REPO_SYNC_TOKEN", None)


if __name__ == "__main__":
    unittest.main()