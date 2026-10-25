import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import ast
from skills.anomaly_autofixer import AnomalyAutofixer, AnomalyAutofixerError, autofix_anomalies


class TestAnomalyAutofixerInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = round(random.uniform(0.1, 0.9), 2)
        self.autofixer = AnomalyAutofixer(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def test_dispatch_and_fix_success(self):
        source_name = f"src_{uuid.uuid4().hex}"
        severity_level = random.choice(["HIGH", "CRITICAL", "MEDIUM"])
        details_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot_dict = {uuid.uuid4().hex: random.randint(1, 100)}
        expected_patch_id = f"patch_{uuid.uuid4().hex}"

        with patch("skills.anomaly_autofixer.AnomalyAuditHub") as mock_audit_hub_cls, \
             patch("skills.anomaly_autofixer.PatchAutocorrector") as mock_patch_corrector_cls:

            mock_audit_hub_instance = mock_audit_hub_cls.return_value
            mock_patch_corrector_instance = mock_patch_corrector_cls.return_value
            mock_patch_corrector_instance.apply_fix.return_value = expected_patch_id

            autofixer_local = AnomalyAutofixer(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

            result_patch_id = autofixer_local.dispatch_and_fix(
                source=source_name,
                severity=severity_level,
                details=details_dict,
                telemetry_snapshot=telemetry_snapshot_dict
            )

            mock_audit_hub_instance.log_anomaly.assert_called_once_with(
                source_name, severity_level, details_dict, telemetry_snapshot_dict
            )
            mock_audit_hub_instance.generate_final_report.assert_called_once()
            mock_patch_corrector_instance.apply_fix.assert_called_once()
            self.assertEqual(result_patch_id, expected_patch_id)

    def test_dispatch_and_fix_failure_raises_error(self):
        source_name = f"src_{uuid.uuid4().hex}"
        severity_level = random.choice(["LOW", "WARNING"])
        details_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot_dict = {uuid.uuid4().hex: random.randint(101, 200)}
        error_msg = f"err_{uuid.uuid4().hex}"

        with patch("skills.anomaly_autofixer.AnomalyAuditHub") as mock_audit_hub_cls:
            mock_audit_hub_instance = mock_audit_hub_cls.return_value
            mock_audit_hub_instance.log_anomaly.side_effect = Exception(error_msg)

            autofixer_local = AnomalyAutofixer(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

            with self.assertRaises(AnomalyAutofixerError) as ctx:
                autofixer_local.dispatch_and_fix(
                    source=source_name,
                    severity=severity_level,
                    details=details_dict,
                    telemetry_snapshot=telemetry_snapshot_dict
                )

            self.assertIn(error_msg, str(ctx.exception))

    def test_analyze_log_stream_success(self):
        random_bytes = uuid.uuid4().hex.encode('utf-8')

        with patch("builtins.open", return_value=io.BytesIO(random_bytes)) as mock_file:
            content = self.autofixer.analyze_log_stream()
            mock_file.assert_called_once_with(self.log_path, "rb")
            self.assertEqual(content, random_bytes)

    def test_autofix_anomalies_function(self):
        random_repo = f"/repo/{uuid.uuid4().hex}"
        random_patch_id = f"patch_{uuid.uuid4().hex}"
        audit_report_dict = {uuid.uuid4().hex: uuid.uuid4().hex, uuid.uuid4().hex: uuid.uuid4().hex}
        metadata_dict = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.anomaly_autofixer.PatchAutocorrector") as mock_corrector_cls:
            mock_corrector_instance = mock_corrector_cls.return_value
            mock_corrector_instance.apply_fix.return_value = random_patch_id

            result = autofix_anomalies(
                repo_path=random_repo,
                audit_report=audit_report_dict,
                metadata=metadata_dict
            )

            mock_corrector_cls.assert_called_once_with(repo_path=random_repo)
            mock_corrector_instance.apply_fix.assert_called_once()

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["repo_path"], random_repo)
            self.assertEqual(result["patch_id"], random_patch_id)
            self.assertEqual(set(result["report_keys"]), set(audit_report_dict.keys()))
            self.assertEqual(result["metadata"], metadata_dict)


if __name__ == "__main__":
    unittest.main()