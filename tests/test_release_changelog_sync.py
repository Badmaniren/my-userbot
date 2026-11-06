import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from skills.release_changelog_sync import ReleaseChangelogSync, sync_release_changelog


class TestReleaseChangelogSync(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.changelog_content = f"# Changelog\n- {uuid.uuid4().hex}"
        self.external_url = f"https://example.com/api/{uuid.uuid4().hex}"

    def test_init_defaults(self):
        syncer = ReleaseChangelogSync()
        self.assertIsNone(syncer.repo_sync)
        self.assertIsNone(syncer.release_notes_publisher)

    def test_sync_changelog_invalid_parameters(self):
        syncer = ReleaseChangelogSync()
        with self.assertRaises(ValueError):
            syncer.sync_changelog("", self.changelog_content, self.external_url)
        with self.assertRaises(ValueError):
            syncer.sync_changelog(self.repo_path, "", self.external_url)
        with self.assertRaises(ValueError):
            syncer.sync_changelog(None, None, self.external_url)

    def test_sync_changelog_with_sync_id(self):
        expected_sync_id = uuid.uuid4().hex
        mock_repo_sync = MagicMock()
        mock_publisher = MagicMock()

        syncer = ReleaseChangelogSync(
            repo_sync=mock_repo_sync,
            release_notes_publisher=mock_publisher
        )

        with patch("skills.release_changelog_sync.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"sync_id": expected_sync_id}
            mock_post.return_value = mock_response

            result = syncer.sync_changelog(
                self.repo_path,
                self.changelog_content,
                self.external_url
            )

            mock_repo_sync.push.assert_called_once_with(self.repo_path)
            mock_publisher.publish.assert_called_once_with(self.changelog_content)
            mock_post.assert_called_once_with(
                self.external_url,
                json={"changelog": self.changelog_content, "repo_path": self.repo_path}
            )
            self.assertEqual(result, expected_sync_id)

    def test_sync_changelog_without_sync_id(self):
        mock_repo_sync = MagicMock()
        mock_publisher = MagicMock()

        syncer = ReleaseChangelogSync(
            repo_sync=mock_repo_sync,
            release_notes_publisher=mock_publisher
        )

        with patch("skills.release_changelog_sync.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": uuid.uuid4().hex}
            mock_post.return_value = mock_response

            result = syncer.sync_changelog(
                self.repo_path,
                self.changelog_content,
                self.external_url
            )

            mock_repo_sync.push.assert_called_once_with(self.repo_path)
            mock_publisher.publish.assert_called_once_with(self.changelog_content)
            self.assertTrue(result)

    def test_sync_changelog_no_optional_dependencies(self):
        syncer = ReleaseChangelogSync()

        with patch("skills.release_changelog_sync.requests.post") as mock_post:
            expected_sync_id = uuid.uuid4().hex
            mock_response = MagicMock()
            mock_response.json.return_value = {"sync_id": expected_sync_id}
            mock_post.return_value = mock_response

            result = syncer.sync_changelog(
                self.repo_path,
                self.changelog_content,
                self.external_url
            )

            self.assertEqual(result, expected_sync_id)

    def test_sync_release_changelog_payload(self):
        version = f"v{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        notes = f"Release notes: {uuid.uuid4().hex}"
        sync_id = uuid.uuid4().hex

        payload = {
            "version": version,
            "notes": notes,
            "sync_id": sync_id
        }

        result = sync_release_changelog(payload)

        self.assertEqual(result["status"], "synced")
        self.assertEqual(result["version"], version)
        self.assertEqual(result["sync_id"], sync_id)
        self.assertEqual(result["notes"], notes)

    def test_sync_release_changelog_empty_payload(self):
        result = sync_release_changelog({})

        self.assertEqual(result["status"], "synced")
        self.assertIsNone(result["version"])
        self.assertEqual(result["sync_id"], "")
        self.assertIsNone(result["notes"])


if __name__ == "__main__":
    unittest.main()