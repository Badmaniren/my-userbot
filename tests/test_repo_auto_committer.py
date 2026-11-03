import unittest
from unittest.mock import patch
import uuid
import random
from skills.repo_auto_committer import RepoAutoCommitter


class TestRepoAutoCommitter(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.auto_committer = RepoAutoCommitter(self.random_repo_path)

    def test_init_sets_repo_path_and_components(self):
        self.assertEqual(self.auto_committer.repo_path, self.random_repo_path)
        self.assertEqual(self.auto_committer.monitor.repo_path, self.random_repo_path)
        self.assertEqual(self.auto_committer.summarizer.repo_path, self.random_repo_path)
        self.assertEqual(self.auto_committer.committer.repo_path, self.random_repo_path)

    def test_run_no_changes_returns_false(self):
        with patch.object(self.auto_committer.monitor, 'check_status') as mock_check, \
             patch.object(self.auto_committer.summarizer, 'generate_summary') as mock_summary, \
             patch.object(self.auto_committer.committer, 'commit') as mock_commit:

            mock_check.return_value = ""

            result = self.auto_committer.run()

            self.assertFalse(result)
            mock_check.assert_called_once()
            mock_summary.assert_not_called()
            mock_commit.assert_not_called()

    def test_run_whitespace_changes_returns_false(self):
        with patch.object(self.auto_committer.monitor, 'check_status') as mock_check, \
             patch.object(self.auto_committer.summarizer, 'generate_summary') as mock_summary, \
             patch.object(self.auto_committer.committer, 'commit') as mock_commit:

            mock_check.return_value = "   \n\t  "

            result = self.auto_committer.run()

            self.assertFalse(result)
            mock_check.assert_called_once()
            mock_summary.assert_not_called()
            mock_commit.assert_not_called()

    def test_run_with_changes_success(self):
        random_changes = f"file_{uuid.uuid4().hex}.py modified"
        random_summary = f"feat: update {uuid.uuid4().hex}"
        commit_result = random.choice([True, False])

        with patch.object(self.auto_committer.monitor, 'check_status') as mock_check, \
             patch.object(self.auto_committer.summarizer, 'generate_summary') as mock_summary, \
             patch.object(self.auto_committer.committer, 'commit') as mock_commit:

            mock_check.return_value = random_changes
            mock_summary.return_value = random_summary
            mock_commit.return_value = commit_result

            result = self.auto_committer.run()

            self.assertEqual(result, bool(commit_result))
            mock_check.assert_called_once()
            mock_summary.assert_called_once()
            mock_commit.assert_called_once_with(random_summary)

    def test_process_and_commit_alias(self):
        random_changes = f"changes_{uuid.uuid4().hex}"
        random_summary = f"fix: bug {uuid.uuid4().hex}"

        with patch.object(self.auto_committer.monitor, 'check_status') as mock_check, \
             patch.object(self.auto_committer.summarizer, 'generate_summary') as mock_summary, \
             patch.object(self.auto_committer.committer, 'commit') as mock_commit:

            mock_check.return_value = random_changes
            mock_summary.return_value = random_summary
            mock_commit.return_value = True

            result = self.auto_committer.process_and_commit()

            self.assertTrue(result)
            mock_check.assert_called_once()
            mock_summary.assert_called_once()
            mock_commit.assert_called_once_with(random_summary)


if __name__ == '__main__':
    unittest.main()