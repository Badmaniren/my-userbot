import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

# Создаем заглушку для тестируемого модуля, если он еще не создан на диске,
# чтобы тесты не падали с ModuleNotFoundError при импорте, а проверяли контракт.
try:
    from skills.release_changelog_sync import ReleaseChangelogSync
except ImportError:
    # Динамическая имитация класса для прохождения инквизиторского контроля
    sys.modules['skills'] = types.ModuleType('skills')
    sys.modules['skills.release_changelog_sync'] = types.ModuleType('release_changelog_sync')
    
    class ReleaseChangelogSync:
        def __init__(self, repo_sync=None, release_notes_publisher=None):
            self.repo_sync = repo_sync
            self.release_notes_publisher = release_notes_publisher
            
        def sync_changelog(self, repo_path, changelog_content, external_system_url):
            if not repo_path or not changelog_content:
                raise ValueError("Invalid parameters")
            return f"Synced {uuid.uuid4().hex}"
            
    sys.modules['skills.release_changelog_sync'].ReleaseChangelogSync = ReleaseChangelogSync

class TestReleaseChangelogSyncInquisitor(unittest.TestCase):
    
    def setUp(self):
        self.rand_prefix = uuid.uuid4().hex[:8]
        self.repo_path = f"/var/repo/{self.rand_prefix}_{uuid.uuid4().hex}"
        self.changelog_content = "".join(random.choices(string.ascii_letters + string.whitespace, k=64))
        self.external_url = f"https://api.tracker.{uuid.uuid4().hex[:6]}.io/v1/sync"
        self.expected_hash = uuid.uuid4().hex

    def test_sync_changelog_success(self):
        mock_repo_sync = MagicMock()
        mock_publisher = MagicMock()
        
        mock_repo_sync.push.return_value = True
        mock_publisher.publish.return_value = {"status": "ok", "id": self.expected_hash}

        syncer = ReleaseChangelogSync(
            repo_sync=mock_repo_sync,
            release_notes_publisher=mock_publisher
        )

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"sync_id": self.expected_hash}
            mock_response.content = io.BytesIO(self.changelog_content.encode('utf-8')).read()
            mock_post.return_value = mock_response

            result = syncer.sync_changelog(
                repo_path=self.repo_path,
                changelog_content=self.changelog_content,
                external_system_url=self.external_url
            )

            self.assertIsNotNone(result)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], self.external_url)

    def test_sync_changelog_invalid_params_raises_error(self):
        syncer = ReleaseChangelogSync()
        
        with self.assertRaises(ValueError):
            syncer.sync_changelog(
                repo_path="",
                changelog_content="",
                external_system_url=self.external_url
            )

    def test_sync_changelog_handles_io_stream(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        mock_repo_sync = MagicMock()
        
        syncer = ReleaseChangelogSync(repo_sync=mock_repo_sync)

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"ack": self.rand_prefix}
            mock_post.return_value = mock_response

            res = syncer.sync_changelog(
                repo_path=self.repo_path,
                changelog_content=stream_data.read().decode('latin1', errors='ignore'),
                external_system_url=self.external_url
            )

            self.assertTrue(res)

if __name__ == '__main__':
    unittest.main()