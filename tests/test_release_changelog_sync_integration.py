import unittest
import uuid
import random
import tempfile
import os
from unittest.mock import patch, MagicMock

from skills.release_changelog_sync import ReleaseChangelogSync, sync_release_changelog
from skills.repo_sync import repo_sync
from skills.release_notes_publisher import release_notes_publisher


class TestReleaseChangelogSyncIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        
        self.random_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_notes = f"Changelog entry notes {uuid.uuid4()}"
        self.random_sync_id = str(uuid.uuid4())
        self.external_url = f"https://api.external-tracker.internal/v1/sync/{uuid.uuid4()}"

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('skills.release_changelog_sync.requests.post')
    def test_sync_changelog_integration_real_flow(self, mock_requests_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"sync_id": self.random_sync_id, "status": "success"}
        mock_requests_post.return_value = mock_response

        real_repo_sync = repo_sync() if callable(repo_sync) else None
        real_publisher = release_notes_publisher() if callable(release_notes_publisher) else None

        syncer = ReleaseChangelogSync(
            repo_sync=real_repo_sync,
            release_notes_publisher=real_publisher
        )

        result_id = syncer.sync_changelog(
            repo_path=self.repo_path,
            changelog_content=self.random_notes,
            external_system_url=self.external_url
        )

        self.assertEqual(result_id, self.random_sync_id)

        mock_requests_post.assert_called_once()
        called_url, called_kwargs = mock_requests_post.call_args
        self.assertEqual(called_url[0], self.external_url)
        self.assertEqual(
            called_kwargs.get("json"),
            {"changelog": self.random_notes, "repo_path": self.repo_path}
        )

        payload = {
            "version": self.random_version,
            "notes": self.random_notes,
            "sync_id": result_id
        }
        sync_result = sync_release_changelog(payload)

        self.assertEqual(sync_result["status"], "synced")
        self.assertEqual(sync_result["version"], self.random_version)
        self.assertEqual(sync_result["sync_id"], self.random_sync_id)
        self.assertEqual(sync_result["notes"], self.random_notes)


if __name__ == "__main__":
    unittest.main()