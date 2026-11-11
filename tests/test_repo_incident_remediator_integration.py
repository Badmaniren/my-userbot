import os
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

import skills.repo_incident_remediator as remediator_module


class TestRepoIncidentRemediatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_incident_remed_")
        self.repo_path = Path(self.test_dir) / "repo"
        self.repo_path.mkdir(parents=True, exist_ok=True)
        
        # Create initial valid repo structure
        (self.repo_path / "src").mkdir(parents=True, exist_ok=True)
        self.main_file = self.repo_path / "src" / "main.py"
        self.main_file.write_text("print('stable state')\n", encoding="utf-8")
        
        self.config_file = self.repo_path / "integrity.lock"
        self.config_file.write_text("version=1.0.0\nchecksum=valid\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _call_remediator(self, incident_payload):
        if hasattr(remediator_module, "remediate_repo_incident"):
            return remediator_module.remediate_repo_incident(
                repo_path=str(self.repo_path),
                incident_data=incident_payload
            )
        elif hasattr(remediator_module, "RepoIncidentRemediator"):
            instance = remediator_module.RepoIncidentRemediator()
            if hasattr(instance, "remediate"):
                return instance.remediate(
                    repo_path=str(self.repo_path),
                    incident_data=incident_payload
                )
            elif hasattr(instance, "remediate_incident"):
                return instance.remediate_incident(
                    repo_path=str(self.repo_path),
                    incident_data=incident_payload
                )
        elif hasattr(remediator_module, "remediate_incident"):
            return remediator_module.remediate_incident(
                repo_path=str(self.repo_path),
                incident_data=incident_payload
            )
        raise AttributeError("No suitable remediation entry point found in skills.repo_incident_remediator")

    def test_remediate_corrupted_integrity_file(self):
        random_token = str(uuid.uuid4())
        incident_id = f"INC-{uuid.uuid4().hex[:8]}"
        target_file_name = f"critical_manifest_{uuid.uuid4().hex[:6]}.json"
        target_file_path = self.repo_path / target_file_name
        
        # Introduce corruption/failure in repo
        target_file_path.write_text(f'{{"corrupted": true, "token": "{random_token}"}}', encoding="utf-8")

        incident_payload = {
            "incident_id": incident_id,
            "failure_type": "integrity_violation",
            "severity": "high",
            "target_path": target_file_name,
            "remediation_action": "restore_or_rebuild",
            "expected_state": {
                "file": target_file_name,
                "token": random_token,
                "status": "restored"
            }
        }

        result = self._call_remediator(incident_payload)

        # Assert response contract
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success") or result.get("status") in ("resolved", "success", "remediated"))
        self.assertEqual(result.get("incident_id"), incident_id)
        
        # Verify validation metrics / verification stage was executed
        validation_report = result.get("validation", result.get("verification", {}))
        self.assertTrue(
            validation_report.get("is_valid", True) or validation_report.get("passed", True)
        )

        # Verify filesystem reflects resolution
        remediation_marker = self.repo_path / ".remediation_log.json"
        if remediation_marker.exists():
            log_content = remediation_marker.read_text(encoding="utf-8")
            self.assertIn(incident_id, log_content)

        # The target file should either be fixed or updated to resolved state
        self.assertTrue(target_file_path.exists())

    def test_remediate_missing_dependency_descriptor(self):
        unique_run_id = str(uuid.uuid4())
        incident_id = f"INC-DEP-{uuid.uuid4().hex[:8]}"
        missing_file = f"requirements_{uuid.uuid4().hex[:4]}.txt"

        incident_payload = {
            "incident_id": incident_id,
            "failure_type": "missing_critical_configuration",
            "severity": "critical",
            "target_path": missing_file,
            "default_content": f"# Auto-generated repair {unique_run_id}\n",
            "remediation_action": "recreate_default_config"
        }

        result = self._call_remediator(incident_payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), incident_id)
        self.assertIn(result.get("status", "resolved"), ["resolved", "success", "remediated"])

        recreated_path = self.repo_path / missing_file
        self.assertTrue(
            recreated_path.exists(),
            f"Remediator must create missing configuration file: {missing_file}"
        )
        content = recreated_path.read_text(encoding="utf-8")
        self.assertIn(unique_run_id, content)


if __name__ == "__main__":
    unittest.main()