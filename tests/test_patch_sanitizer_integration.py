import unittest
import uuid
import random
import os
import tempfile
from skills.patch_sanitizer import sanitize_patch
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestPatchSanitizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, f"anomaly_{uuid.uuid4()}.log")
        self.repo_path = self.test_dir.name
        self.audit_hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_path, threshold=random.randint(5, 10))
        self.anomaly_logger = AnomalyLogger(log_path=self.log_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_patch_sanitizer_integration_flow(self):
        unique_patch_id = str(uuid.uuid4())
        random_payload_size = random.randint(100, 2000)
        malicious_content = f"// MALICIOUS INJECTION {unique_patch_id}\n" + "A" * random_payload_size
        
        raw_patch = (
            f"diff --git a/target_{unique_patch_id}.py b/target_{unique_patch_id}.py\n"
            f"index {uuid.uuid4().hex[:7]}..{uuid.uuid4().hex[:7]} 100644\n"
            f"--- a/target_{unique_patch_id}.py\n"
            f"+++ b/target_{unique_patch_id}.py\n"
            f"@@ -1,1 +1,2 @@\n"
            f" {malicious_content}"
        )

        sanitized_result = sanitize_patch(raw_patch)
        
        self.assertIsNotNone(sanitized_result, "Sanitizer returned None for valid input structure.")
        
        if len(sanitized_result) < len(raw_patch):
            severity = "HIGH"
            details = f"Patch {unique_patch_id} was normalized or scrubbed for anomalies."
        else:
            severity = "LOW"
            details = f"Patch {unique_patch_id} passed normalization cleanly."

        telemetry_snapshot = {
            "payload_size": random_payload_size,
            "uuid_marker": unique_patch_id,
            "entropy": random.uniform(0.1, 0.9)
        }

        self.audit_hub.log_anomaly(
            source="patch_sanitizer",
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        aggregated_metric = self.audit_hub.aggregate_and_report(
            metric_name=f"sanitization_check_{unique_patch_id[:8]}",
            value=float(random_payload_size)
        )
        self.assertIsNotNone(aggregated_metric)

        report = self.audit_hub.generate_final_report()
        self.assertIsInstance(report, (dict, str, list))

        logged_anomalies = self.anomaly_logger.get_anomalies()
        self.assertTrue(len(logged_anomalies) > 0, "Anomaly logger failed to record audit events from real integration.")
        
        found_target = False
        for anomaly in logged_anomalies:
            if unique_patch_id in str(anomaly):
                found_target = True
                break
        
        self.assertTrue(found_target, f"Expected unique identifier {unique_patch_id} not found in anomaly logs.")

if __name__ == '__main__':
    unittest.main()