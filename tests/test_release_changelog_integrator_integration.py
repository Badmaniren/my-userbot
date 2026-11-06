import unittest
import os
import shutil
import tempfile
import uuid
import random
import sys
import types

mock_modules = [
    'vulnerability_analyzer',
    'dependency_updater_pipeline',
    'repo_reporter'
]
for mod_name in mock_modules:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = types.ModuleType(mod_name)

from skills.release_changelog_integrator import ReleaseChangelogIntegrator, release_changelog_integrator


class TestReleaseChangelogIntegratorIntegration(unittest.TestCase):
    def setUp(self):
        self.integrator = ReleaseChangelogIntegrator()
        self.random_uuid = str(uuid.uuid4())
        self.random_version = f"v{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.test_repo_path = tempfile.mkdtemp(prefix="test_repo_")

    def tearDown(self):
        if os.path.exists(self.test_repo_path):
            shutil.rmtree(self.test_repo_path)

    def test_parse_changelog_file_integration(self):
        test_file = os.path.join(self.test_repo_path, f"CHANGELOG_{self.random_uuid}.md")
        content = f"# Changelog\nRelease {self.random_version}\nNotes: {self.random_uuid}\n"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(content)

        parsed = self.integrator.parse_changelog_file(test_file)
        self.assertEqual(parsed, content)

    def test_release_changelog_integrator_functional_integration(self):
        rand_status = f"status_{uuid.uuid4().hex[:6]}"
        payload = {
            "repo_path": self.test_repo_path,
            "target_version": self.random_version,
            "integration_id": self.random_uuid,
            "hub_status": rand_status
        }
        res = release_changelog_integrator(payload)
        self.assertEqual(res["status"], "synchronized")
        self.assertEqual(res["integration_id"], self.random_uuid)
        self.assertEqual(res["version"], self.random_version)

        expected_file = os.path.join(self.test_repo_path, "CHANGELOG.md")
        self.assertTrue(os.path.exists(expected_file))
        with open(expected_file, "r", encoding="utf-8") as f:
            file_content = f.read()

        self.assertIn(self.random_version, file_content)
        self.assertIn(self.random_uuid, file_content)
        self.assertIn(rand_status, file_content)


if __name__ == "__main__":
    unittest.main()
