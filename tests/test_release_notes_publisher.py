import unittest
from unittest.mock import patch, MagicMock
import os
import random
import uuid
from skills.release_notes_publisher import ReleaseNotesPublisher


class TestReleaseNotesPublisher(unittest.TestCase):

    def setUp(self):
        self.repo_path = os.path.join('/tmp', uuid.uuid4().hex)
        self.output_path = os.path.join('/tmp', uuid.uuid4().hex, f"{uuid.uuid4().hex}.md")
        self.expected_result = random.choice([True, False])
        self.expected_compose_result = uuid.uuid4().hex

    def test_init_sets_repo_path(self):
        with patch('skills.release_notes_publisher.ReleaseNotesComposer') as mock_composer, \
             patch('skills.release_notes_publisher.RepoNotifier') as mock_notifier:
            publisher = ReleaseNotesPublisher(self.repo_path)
            self.assertEqual(publisher.repo_path, self.repo_path)
            mock_composer.assert_called_once_with(self.repo_path)
            mock_notifier.assert_called_once_with(self.repo_path)

    def test_publish_success(self):
        with patch('skills.release_notes_publisher.ReleaseNotesComposer') as mock_composer_cls, \
             patch('skills.release_notes_publisher.RepoNotifier') as mock_notifier_cls, \
             patch('os.makedirs') as mock_makedirs:
            
            mock_composer = mock_composer_cls.return_value
            mock_composer.compose.return_value = self.expected_compose_result
            
            mock_notifier = mock_notifier_cls.return_value
            mock_notifier.notify.return_value = self.expected_result

            publisher = ReleaseNotesPublisher(self.repo_path)
            res = publisher.publish(self.output_path)

            mock_makedirs.assert_called_once_with(os.path.dirname(self.output_path), exist_ok=True)
            mock_composer.compose.assert_called_once_with(self.output_path)
            mock_notifier.notify.assert_called_once_with(self.output_path)
            self.assertEqual(res, self.expected_result)

    def test_publish_composer_fails(self):
        with patch('skills.release_notes_publisher.ReleaseNotesComposer') as mock_composer_cls, \
             patch('skills.release_notes_publisher.RepoNotifier') as mock_notifier_cls, \
             patch('os.makedirs'):
            
            mock_composer = mock_composer_cls.return_value
            random_error_msg = uuid.uuid4().hex
            mock_composer.compose.side_effect = Exception(random_error_msg)
            
            publisher = ReleaseNotesPublisher(self.repo_path)
            
            with self.assertRaises(Exception) as ctx:
                publisher.publish(self.output_path)
            
            self.assertIn(random_error_msg, str(ctx.exception))

    def test_run_executes_workflow(self):
        with patch('skills.release_notes_publisher.ReleaseNotesComposer') as mock_composer_cls, \
             patch('skills.release_notes_publisher.RepoNotifier') as mock_notifier_cls:
            
            mock_composer = mock_composer_cls.return_value
            mock_notifier = mock_notifier_cls.return_value
            mock_notifier.notify_and_commit.return_value = self.expected_result

            publisher = ReleaseNotesPublisher(self.repo_path)
            res = publisher.run()

            mock_composer.run.assert_called_once()
            mock_notifier.notify_and_commit.assert_called_once()
            self.assertEqual(res, self.expected_result)

    def test_generate_and_notify(self):
        with patch('skills.release_notes_publisher.ReleaseNotesComposer') as mock_composer_cls, \
             patch('skills.release_notes_publisher.RepoNotifier') as mock_notifier_cls, \
             patch('os.makedirs') as mock_makedirs:
            
            mock_composer = mock_composer_cls.return_value
            mock_composer.generate.return_value = self.expected_compose_result
            
            mock_notifier = mock_notifier_cls.return_value
            mock_notifier.notify.return_value = self.expected_result

            publisher = ReleaseNotesPublisher(self.repo_path)
            res = publisher.generate_and_notify(self.output_path)

            mock_makedirs.assert_called_once_with(os.path.dirname(self.output_path), exist_ok=True)
            mock_composer.generate.assert_called_once_with(self.output_path)
            mock_notifier.notify.assert_called_once_with(self.output_path)
            self.assertEqual(res, self.expected_result)

    def test_compose_and_notify_delegates_to_publish(self):
        with patch('skills.release_notes_publisher.ReleaseNotesPublisher.publish') as mock_publish:
            mock_publish.return_value = self.expected_result

            publisher = ReleaseNotesPublisher(self.repo_path)
            res = publisher.compose_and_notify(self.output_path)

            mock_publish.assert_called_once_with(self.output_path)
            self.assertEqual(res, self.expected_result)


if __name__ == '__main__':
    unittest.main()