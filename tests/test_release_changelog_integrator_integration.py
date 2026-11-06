import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.release_changelog_integrator import release_changelog_integrator
from skills.release_automation_hub import release_automation_hub
from skills.changelog_generator import changelog_generator

class TestReleaseChangelogIntegratorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.random_id = str(uuid.uuid4())
        self.version_tag = f"v1.{random.randint(0, 100)}.{random.randint(0, 100)}"
        self.commit_message = f"chore(release): prepare release {self.random_id}"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_changelog_hub_real_integration(self):
        context = {
            "repo_path": self.test_dir,
            "session_id": self.random_id,
            "version": self.version_tag,
            "notes": f"Automated release notes for run {self.random_id}"
        }

        gen_result = changelog_generator(context)
        
        hub_context = {
            "repo_path": self.test_dir,
            "version": self.version_tag,
            "pipeline_id": self.random_id,
            "changelog_data": gen_result
        }
        hub_status = release_automation_hub(hub_context)

        integrator_input = {
            "repo_path": self.test_dir,
            "target_version": self.version_tag,
            "integration_id": self.random_id,
            "hub_status": hub_status
        }

        integration_result = release_changelog_integrator(integrator_input)

        self.assertIsInstance(integration_result, dict)
        self.assertIn("status", integration_result)
        self.assertEqual(integration_result.get("integration_id"), self.random_id)
        self.assertEqual(integration_result.get("version"), self.version_tag)
        self.assertEqual(integration_result.get("status"), "synchronized")

        changelog_file_path = os.path.join(self.test_dir, "CHANGELOG.md")
        self.assertTrue(os.path.exists(changelog_file_path), "Integration must physically generate or update CHANGELOG.md in the repo path")

        with open(changelog_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.random_id, content, "Generated changelog must contain the unique session identifier")
            self.assertIn(self.version_tag, content, "Generated changelog must contain the target version tag")

if __name__ == "__main__":
    unittest.main()