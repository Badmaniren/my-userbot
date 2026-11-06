import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.release_changelog_sync import sync_release_changelog
from skills.release_notes_composer import compose_release_notes
from skills.git_committer import commit_changes
from skills.repo_logger import log_repository_event

class TestIntegrationReleaseChangelogSync(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        self.random_issue_id = f"ISSUE-{random.randint(1000, 9999)}"
        self.random_version = f"v1.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_commit_msg = f"feat: add synchronization logic {uuid.uuid4()}"

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def test_release_changelog_sync_integration(self):
        os.makedirs(".git", exist_ok=True)
        
        dummy_file = os.path.join(self.test_dir, "change_log_source.txt")
        with open(dummy_file, "w", encoding="utf-8") as f:
            f.write(f"Release {self.random_version}: {self.random_issue_id}")

        composed_notes = compose_release_notes({
            "version": self.random_version,
            "source_path": dummy_file,
            "identifier": self.random_issue_id
        })

        self.assertIsNotNone(composed_notes)

        commit_result = commit_changes({
            "message": self.random_commit_msg,
            "paths": [dummy_file]
        })

        self.assertTrue(commit_result or isinstance(commit_result, dict))

        sync_result = sync_release_changelog({
            "version": self.random_version,
            "notes": composed_notes,
            "target_system": "external_tracker",
            "sync_id": str(uuid.uuid4())
        })

        self.assertIsInstance(sync_result, dict)
        self.assertIn("status", sync_result)
        self.assertEqual(sync_result["status"], "synced")
        self.assertEqual(sync_result.get("version"), self.random_version)

        log_payload = {
            "event": "changelog_synchronized",
            "version": self.random_version,
            "sync_id": sync_result.get("sync_id")
        }
        log_result = log_repository_event(log_payload)
        self.assertIsNotNone(log_result)

if __name__ == "__main__":
    unittest.main()